from django.template.context_processors import request
from rest_framework import serializers
from apps.subscriptions.models import Subscription
from utils.enums import SubscriptionStatus, PriceHistorySource
from .price_serializer import PriceInputSerializer
from .schedule_serializer import ScheduleInputSerializer
from apps.subscriptions.models import Provider, Category
from apps.subscriptions.services.subscription_service import (create_subscription_with_defaults, set_subscription_price,
                                                              PriceInput, ScheduleInput)
from utils.validators import validator_currency

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
            'is_shared',
            'started_at',
            'ended_at',
            'create_at',
            'update_at',
        ]

        read_only_fields = fields


class SubscriptionCreateSerializer(serializers.Serializer):
    """
    Сериализатор для создания подписок
    """
    title = serializers.CharField(max_length=255)
    description = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    status = serializers.ChoiceField(choices=SubscriptionStatus, default=SubscriptionStatus.ACTIVE)
    provider_id = serializers.IntegerField(required=False, allow_null=True)
    category_id = serializers.IntegerField(required=False, allow_null=True)
    started_at = serializers.DateField(required=True, allow_null=True)
    ended_at = serializers.DateField(required=True, allow_null=True)
    billing_timezone = serializers.CharField(max_length=64, required=False, allow_blank=True, allow_null=True)
    payment_method_label = serializers.CharField(max_length=64, required=False, allow_blank=True, allow_null=True)
    owner_note = serializers.CharField(max_length=255, required=False, allow_blank=True, allow_null=True)
    is_shared = serializers.BooleanField(default=False)

    price = PriceInputSerializer()
    schedule = ScheduleInputSerializer()

    def validate_provider_id(self, value):
        if value is None:
            return value

        if Provider.objects.filter(pk=value).exists():
            raise serializers.ValidationError("Provider не найден")

        return value


    def validate_category_id(self, value):
        if value is None:
            return value

        if Category.objects.filter(pk=value).exists():
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

        return create_subscription_with_defaults(
            user = request.user,
            title = validated_data.get('title'),
            description = validated_data.get('description'),
            provider = provider,
            category = category,
            status = validated_data.get('status', SubscriptionStatus.ACTIVE),
            started_at = validated_data.get('started_at'),
            ended_at = validated_data.get('ended_at'),
            billing_timezone  = validated_data.get('billing_timezone'),
            payment_method_label = validated_data.get('payment_method_label'),
            owner_note = validated_data.get('owner_note'),
            is_shared = validated_data.get('is_shared', False),
            price = price_input,
            schedule = schedule_input,
        )


class SubscriptionUpdateSerializer(serializers.ModelSerializer): #TODO Переработать для доменных операций закрытие подписки, даты
    """
    Сериализатор для обновления данных по подписке (!!! Данные по Цене и Расписанию НЕ ОБНОВЛЯЮТСЯ !!!)

    Для обновления Цены используйте SubscriptionSetPriceSerializer
    """
    class Meta:
        model = Subscription
        fields = [
            'title',
            'description',
            'status',
            'provider',
            'category',
            'billing_timezone',
            'payment_method_label',
            'owner_note',
            'is_shared',
            'started_at',
            'ended_at',
        ]


class SubscriptionSetPriceSerializer(PriceInputSerializer):
    """
    Сериализатор для сохранения цены в подписке
    """

    def save(self, subscription):
        price_input = PriceInput(**self.validated_data)
        return set_subscription_price(subscription=subscription,
                                      verified_price=price_input.verified_price,
                                      amount=price_input.amount,
                                      currency=price_input.currency,
                                      effective_from=price_input.effective_from,
                                      reason=price_input.reason,
                                      source=price_input.source)
