from rest_framework import serializers
from django.utils import timezone
from apps.subscriptions.models import Subscription
from utils.enums import SubscriptionStatus
from utils.api.errors import call_service
from .price_serializer import PriceInputSerializer
from .schedule_serializer import ScheduleInputSerializer
from apps.subscriptions.models import Provider, Category
from apps.subscriptions.services.subscription_service import (create_subscription_with_defaults, update_subscription_data,
                                                              set_subscription_price, set_subscription_status,
                                                              PriceInput, ScheduleInput)

#------------------------------------ READ Subscription ------------------------------------
class SubscriptionReadSerializer(serializers.ModelSerializer):
    """
    Сериализатор для получения данных по подпискам
    """
    provider_name = serializers.CharField(source='provider.name', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = Subscription
        fields = [
            'id',
            'title',
            'description',
            'status',
            'provider',
            'provider_name',
            'category',
            'category_name',
            'current_price_amount',
            'current_price_currency',
            'next_billing_at',
            'billing_timezone',
            'last_billed_at',
            'payment_method_label',
            'owner_note',
            'started_at',
            'ended_at',
            'create_at',
            'update_at',
        ]

        read_only_fields = fields


#------------------------------------ CREATE Subscription ------------------------------------
class SubscriptionCreateSerializer(serializers.Serializer):
    """
    Сериализатор для создания подписок
    """
    title = serializers.CharField(max_length=255)
    description = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    provider_id = serializers.IntegerField(required=False, allow_null=True)
    category_id = serializers.IntegerField(required=False, allow_null=True)
    started_at = serializers.DateTimeField(required=True, allow_null=True)
    ended_at = serializers.DateTimeField(required=False, allow_null=True)
    billing_timezone = serializers.CharField(max_length=64, required=False, allow_blank=False, allow_null=False)
    payment_method_label = serializers.CharField(max_length=64, required=False, allow_blank=True, allow_null=True)
    owner_note = serializers.CharField(max_length=255, required=False, allow_blank=True, allow_null=True)

    price = PriceInputSerializer()
    schedule = ScheduleInputSerializer()

    def validate_provider_id(self, value):
        if value is None:
            return value
        if not Provider.objects.filter(pk=value).exists():
            raise serializers.ValidationError("Provider не найден")
        return value


    def validate_category_id(self, value):
        if value is None:
            return value
        if not Category.objects.filter(pk=value).exists():
            raise serializers.ValidationError("Category не найден")
        return value


    def create(self, validated_data):
        request = self.context['request']

        price_data = validated_data.pop('price')
        schedule_data = validated_data.pop('schedule')

        provider = None
        provider_id = validated_data.pop('provider_id', None)
        if provider_id is not None:
            provider = Provider.objects.get(pk=provider_id)

        category = None
        category_id = validated_data.pop('category_id', None)
        if category_id is not None:
            category = Category.objects.get(pk=category_id)

        price_input = PriceInput(**price_data)
        schedule_input = ScheduleInput(**schedule_data)

        return call_service(
            create_subscription_with_defaults,
            user = request.user,
            title = validated_data.get('title'),
            description = validated_data.get('description'),
            provider = provider,
            category = category,
            started_at = validated_data.get('started_at'),
            ended_at = validated_data.get('ended_at'),
            billing_timezone  = validated_data.get('billing_timezone'),
            payment_method_label = validated_data.get('payment_method_label'),
            owner_note = validated_data.get('owner_note'),
            price = price_input,
            schedule = schedule_input,
        )


#------------------------------------ UPDATE Subscription ------------------------------------
class SubscriptionUpdateSerializer(serializers.Serializer):
    """
    Сериализатор для обновления данных по подписке (!!! Данные по Цене и Расписанию НЕ ОБНОВЛЯЮТСЯ !!!)

    Для обновления Цены используйте SubscriptionSetPriceSerializer
    """
    title = serializers.CharField(max_length=255, required=False)
    description = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    category_id = serializers.IntegerField(required=False, allow_null=True)

    billing_timezone = serializers.CharField(max_length=64, required=False, allow_blank=False, allow_null=False)

    payment_method_label = serializers.CharField(max_length=64, required=False, allow_blank=True, allow_null=True)
    owner_note = serializers.CharField(max_length=255, required=False, allow_blank=True, allow_null=True)

    def validate_category_id(self, value):
        if value is None:
            return value
        if not Category.objects.filter(pk=value).exists():
            raise serializers.ValidationError("Category не найден")
        return value

    def update(self, instance, validated_data):
        category = instance.category
        if 'category_id' in validated_data:
            category_id = validated_data.pop('category_id')
            category = Category.objects.get(pk=category_id) if category_id else None

        return call_service(
            update_subscription_data,
            subscription=instance,
            category=category,
            **validated_data
        )


#------------------------------------ SET Price Subscription ------------------------------------
class SubscriptionSetPriceSerializer(PriceInputSerializer):
    """
    Сериализатор для сохранения цены в подписке
    """
    def save(self, subscription):
        price_input = PriceInput(**self.validated_data)

        new_price = call_service(
            set_subscription_price,
            subscription=subscription,
            verified_price=price_input.verified_price,
            amount=price_input.amount,
            currency=price_input.currency,
            effective_from=price_input.effective_from,
            change_reason=price_input.change_reason,
            source=price_input.source
        )

        return new_price.subscription


#------------------------------------ SET Provider Subscription ------------------------------------
class SubscriptionSetProviderSerializer(serializers.Serializer):
    """
    Сериализатор для изменения провайдера в подписке
    """
    pass


#------------------------------------ SET Status Subscription ------------------------------------
class SubscriptionSetStatusSerializer(serializers.Serializer):
    """
    Сериализатор для изменения статуса в подписке
    """
    status = serializers.ChoiceField(required=True, choices=SubscriptionStatus)
    started_at = serializers.DateTimeField(required=False, allow_null=True)

    def validate(self, attrs):
        status = attrs.get('status')
        started_at = attrs.get('started_at')

        if status == SubscriptionStatus.TRIAL:
            raise serializers.ValidationError("TRIAL нельзя устанавливать через set_status.")

        if status == SubscriptionStatus.DELAYED:
            if started_at is None:
                raise serializers.ValidationError("Поле started_at является обязательным для статуса DELAYED")
            if started_at <= timezone.now():
                raise serializers.ValidationError("Для статуса DELAYED поле started_at должно быть больше текущей даты")
        else:
            if started_at is not None:
                raise serializers.ValidationError("Поле started_at заполняется исключительно для статуса DELAYED")

        return attrs

    def save(self, subscription):
        return call_service(
            set_subscription_status,
            subscription=subscription,
            status_new=self.validated_data.get('status'),
            started_at=self.validated_data.get('started_at')
        )


#------------------------------------  Cancel Subscription ------------------------------------
class SubscriptionCancelSerializer(serializers.Serializer):
    """
    Сериализатор для завершения подписки
    """
    cancel_mode = serializers.ChoiceField(choices=["immediately", "end_of_period"],
                                          default="end_of_period")

    def save(self, subscription):
        cancel_mode = self.validated_data.get('cancel_mode')
        if cancel_mode == "end_of_period":
            cancel_status = SubscriptionStatus.CANCELED
        elif cancel_mode == "immediately":
            cancel_status = SubscriptionStatus.EXPIRED
        else:
            raise serializers.ValidationError(f"Неизвестный режим {cancel_mode}")

        return call_service(
            set_subscription_status,
            subscription=subscription,
            status_new=cancel_status
        )