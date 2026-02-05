from django.core.validators import ValidationError
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
import re
from pycountry import currencies, countries
from decimal import Decimal
from typing import Optional

from utils.enums import PriceHistorySource

from apps.subscriptions.models.price import VerifiedPrice

_CURRENCY_RE = re.compile(r'^[A-Z]{3}$')   # ISO 4217 (USD/EUR/RUB...)
_COUNTRY_RE = re.compile(r'^[A-Z]{2}$')    # ISO 3166-1 alpha-2 (US, DE, RU, ...) или GLOBAL


def validator_timezone(value: str):
    """
    Валидация IANA timezone ("Asia/Yekaterinburg", "Europe/Moscow"...)
    """
    if value in (None, ''):
        return

    try:
        ZoneInfo(value)
    except ZoneInfoNotFoundError as e:
        raise ValidationError(f'Timezone не существует: {value}') from e


def validator_currency(value: str):
    """
    Валидация валюты ISO 4217 (USD/EUR/RUB...)
    """
    if value in (None, ''):
        raise ValidationError(f'Код валюты обязателен для заполнения')

    # Проверка соответствия формату ISO 4217 alpha-3
    if not _CURRENCY_RE.match(value):
        raise ValidationError(f'Код валюты не соответствует формату ISO 4217')

    if currencies.get(alpha_3=value) is None:
        raise ValidationError(f'Валюта не найдена: {value}')


def validator_region(value: str):
    """
    Валидация региона ISO 3166-1 alpha-2 (US, DE, RU, ...) или GLOBAL
    """
    if value in (None, ''):
        raise ValidationError(f'Регион обязателен для заполнения')

    if value == 'GLOBAL':
        return

    # Проверка соответствия формату ISO 3166-1 alpha-2
    if not _COUNTRY_RE.match(value):
        raise ValidationError(f'Регион не соответствует формату ISO 3166-1 alpha-2 или GLOBAL')

    if countries.get(alpha_2=value) is None:
        raise ValidationError(f'Регион не найден: {value}')


# Перенести в price service
def validator_price_history_source(source: str, verified_price: Optional[VerifiedPrice] = None,
                                   amount: Optional[Decimal] = None, currency: Optional[str] = None):
    """
    Валидация корректности режимов источника цены для PriceHistory
    Manual: Обязательное заполнение полей -> amount, current. Поле verified_price не учитывается.
    Verified: Обязательное заполнение поля -> verified_price. Поля amount, current не учитываются.
    """
    if source == PriceHistorySource.VERIFIED:
        if not verified_price:
            raise ValueError("Verified: verified_price не может отсутствовать")
        if amount is not None and currency is not None:
            raise ValueError("Verified: amount и currency должны быть пустыми")
    elif source == PriceHistorySource.MANUAL:
        if amount is None:
            raise ValueError("Manual: amount обязательное к заполнению")
        if amount <= 0:
            raise ValueError("Цена (amount) не может быть отрицательной.")
        if not currency:
            raise ValueError("Manual: currency обязательное к заполнению")
        if verified_price:
            raise ValueError("Manual: verified_price должна быть пустой")
    else:
        raise ValueError("Некорректный источник цены (price.source). Поддерживаются verified/manual режимы")