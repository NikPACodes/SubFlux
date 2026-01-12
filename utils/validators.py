from django.core.validators import ValidationError
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
import re
from pycountry import currencies, countries

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

    # Проверка соответствия формату ISO 3166-1 alpha-2
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
