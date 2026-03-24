from django.core.validators import ValidationError
from django.utils import timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
import re
from pycountry import currencies, countries
from decimal import Decimal
from typing import Optional

from utils.enums import PriceHistorySource, PeriodUnit, SubscriptionStatus

_CURRENCY_RE = re.compile(r'^[A-Z]{3}$')   # ISO 4217 (USD/EUR/RUB...)
_COUNTRY_RE = re.compile(r'^[A-Z]{2}$')    # ISO 3166-1 alpha-2 (US, DE, RU, ...) или GLOBAL


def validator_timezone(value: str, allow_empty: bool = False):
    """
    Валидация IANA timezone ("Asia/Yekaterinburg", "Europe/Moscow"...)
    """
    if value in (None, ''):
        if allow_empty:
            return
        raise ValidationError(f'Timezone не может быть пустой')

    try:
        ZoneInfo(value)
    except ZoneInfoNotFoundError as e:
        raise ValidationError(f'Некорректная IANA timezone: {value}') from e


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


def validator_price_history_source(source: str, verified_price = None,
                                   amount: Optional[Decimal] = None, currency: Optional[str] = None):
    """
    Валидация корректности режимов источника цены для PriceHistory
    Manual: Обязательное заполнение полей -> amount, current. Поле verified_price не учитывается.
    Verified: Обязательное заполнение поля -> verified_price. Поля amount, current не учитываются.
    """
    if source == PriceHistorySource.VERIFIED:
        if not verified_price:
            raise ValidationError("Verified: verified_price не может отсутствовать")
        if amount is not None or currency is not None:
            raise ValidationError("Verified: amount и currency должны быть пустыми")
    elif source == PriceHistorySource.MANUAL:
        if amount is None:
            raise ValidationError("Manual: amount обязательное к заполнению")
        if amount <= 0:
            raise ValidationError("Цена (amount) не может быть отрицательной.")
        if not currency:
            raise ValidationError("Manual: currency обязательное к заполнению")
        if verified_price:
            raise ValidationError("Manual: verified_price должна быть пустой")
    else:
        raise ValidationError("Некорректный источник цены (price.source). Поддерживаются verified/manual режимы")


def validator_billing_schedule_params(period_unit: str, period_interval: int, anchor_day: Optional[int],
                                      anchor_weekday: Optional[int], grace_days: int):
    """
    Валидация расписания “по смыслу”.

    Назначение:
    - Проверка логических зависимостей
        * поле anchor_day обязательно для MONTH (BillingSchedule.period_unit)
        * поле anchor_weekday обязательно для WEEK (BillingSchedule.period_unit)
        * для DAY/YEAR нет поля якоря
        * проверка интервалов
    """
    if period_interval < 1:
        raise ValidationError("Интервал (каждые N периодов) должен быть >= 1")

    if grace_days < 0:
        raise ValidationError("Льготный период должен быть >= 0")

    if period_unit == PeriodUnit.MONTH and anchor_day is None:
        raise ValidationError("anchor_day является обязательным для интервала (period_unit) по месяцам (MONTH)")
    elif period_unit == PeriodUnit.WEEK and anchor_weekday is None:
        raise ValidationError("anchor_weekday является обязательным для интервала (period_unit) по неделям (WEEK)")


def validator_subscription_status(status: str, started_at, ended_at=None):
    """
    Валидация состояний подписки

    DELAYED -> Отложенное начало подписки
        * started_at > Текущей даты
        * ended_at - Пуст
    ACTIVE -> Активная подписка
        * started_at <= Текущей даты
        * ended_at - Пуст
    CANCELED -> Отменена, но ещё активна
        * started_at <= Текущей даты
        * ended_at >= Текущей даты
    EXPIRED -> Отменена
        * ended_at < Текущей даты

    TODO PAUSED и TRIAL в проработке
    """

    if started_at is None:
        raise ValidationError("Дата начала (started_at) не может быть пустой")
    else:
        if started_at <= timezone.now() and status == SubscriptionStatus.DELAYED:
            raise ValidationError("DELAYED: Дата начала (started_at) должна быть больше текущей даты")
        if started_at > timezone.now() and status != SubscriptionStatus.DELAYED:
            raise ValidationError("Дата начала (started_at) не должна превышать текущую")
        if started_at >= timezone.now() and status == SubscriptionStatus.EXPIRED:
            raise ValidationError("EXPIRED: Дата начала (started_at) должна быть меньше текущей даты")

    if ended_at is None:
        if status in [SubscriptionStatus.CANCELED, SubscriptionStatus.EXPIRED]:
            raise ValidationError("CANCELED/EXPIRED: Дата окончания (ended_at) обязательна к заполнению")
    else:
        if status in [SubscriptionStatus.ACTIVE, SubscriptionStatus.PAUSED]:
            raise ValidationError("ACTIVE/PAUSED: Дата окончания (ended_at) должна быть пустой")
        if ended_at < timezone.now() and status == SubscriptionStatus.CANCELED:
            raise ValidationError("CANCELED: Дата окончания (ended_at) не может быть меньше текущей даты")
        if ended_at >= timezone.now() and status == SubscriptionStatus.EXPIRED:
            raise ValidationError("EXPIRED: Дата окончания (ended_at) должна быть меньше текущей даты")