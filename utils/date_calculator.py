from __future__ import annotations

import calendar
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django.core.exceptions import ValidationError
from django.utils import timezone


def get_tzinfo(tz_name: str | None) -> timezone.tzinfo:
    """
    Получение timezone по IANA-строке.

    Если tz_name пуст берем timezone проекта.
    """

    if not tz_name:
        return timezone.get_current_timezone()

    try:
       return ZoneInfo(tz_name)
    except ZoneInfoNotFoundError as e:
        raise ValidationError(f'Timezone не существует: {tz_name}') from e


def clamp_day_to_month(year: int, month: int, day: int) -> int:
    """
    Корректирует последний день месяца для более коротких месяцев.

    Прим.: “31” в “30” или “28/29” если месяц короче.
    """
    last_day = calendar.monthrange(year, month)[1] # Берем только количество дней
    return min(day, last_day)


def add_months(dtime: datetime, months: int) -> datetime:
    """
    Добавляет N месяцев к datetime сохранением времени.
    """
    # Пояснение логики:
    # Т.к. в месяца начинаются с 1...12
    # При расчете остатка от деления на 12 мы можем получить 0...11
    # Следовательно:
    # 1) либо через if мы должны менять 0 на декабрь
    # 2) либо сначала вычтем 1 месяц а после получения остатка от деления вернем его, и значения будут в интервале 1...12
    total = (dtime.year * 12 + (dtime.month - 1)) + months
    year = total//12
    month = total % 12 + 1
    day = clamp_day_to_month(year, month, dtime.day)
    return dtime.replace(year=year, month=month, day=day)


def next_week(dtime: datetime, interval: int, weekday: int) -> datetime:
    """
    Ищем следующую дату нужного дня недели (weekday 0=Mon...6=Sun) с шагом N недель (interval)
    """
    current = dtime.weekday()
    days_ahead = (weekday - current) % 7
    if days_ahead == 0:
        days_ahead = 7 * interval
    else:
        days_ahead += 7 * (interval - 1)
    return dtime + timedelta(days=days_ahead)
