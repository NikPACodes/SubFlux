from rest_framework import serializers
from apps.subscriptions.models import VerifiedPrice
from utils.enums import PriceHistorySource
from utils.validators import validator_price_history_source, validator_currency
from django.core.exceptions import ValidationError
from utils.api.errors import as_drf_validation_error


class PriceInputSerializer(serializers.Serializer):
    """
    Сериализатор для указания цены в подписке
    """
    source = serializers.ChoiceField(choices=PriceHistorySource, default=PriceHistorySource.MANUAL)
    verified_price_id = serializers.IntegerField(required=False)
    amount = serializers.DecimalField(required=False, max_digits=12, decimal_places=2, allow_null=True,
                                      help_text="Заполняется только для manual-режима.")
    currency = serializers.CharField(required=False, max_length=3, allow_null=True, validators=[validator_currency],
                                     help_text="Заполняется только для manual-режима.")
    effective_from = serializers.DateTimeField(required=False, allow_null=True)
    change_reason = serializers.CharField(max_length=255, required=False, allow_null=True, allow_blank=True)

    def validate(self, attrs):
        verified_price = None

        verified_price_id = attrs.get('verified_price_id')
        # Поиск VerifiedPrice
        if verified_price_id is not None:
            try:
                verified_price = VerifiedPrice.objects.get(pk=verified_price_id, valid_to__isnull=True, is_active=True)
            except VerifiedPrice.DoesNotExist:
                raise serializers.ValidationError('Активная VerifiedPrice не найдена')

        currency = attrs.get('currency')
        # Нормализация Currency
        if currency:
            attrs['currency'] = currency.strip().upper()

        try:
            validator_price_history_source(
                source=attrs.get('source'),
                verified_price=verified_price,
                amount=attrs.get('amount'),
                currency=attrs.get('currency'),
            )
        except ValidationError as exc:
            raise as_drf_validation_error(exc)

        # Нормализация структуры (для корректного создания Subscription)
        attrs['verified_price'] = verified_price
        attrs.pop('verified_price_id', None)
        return  attrs
