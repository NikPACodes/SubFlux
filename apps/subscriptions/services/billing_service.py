"""
Billing service

Функционал:
- валидация расписаний
- расчет next_run_at
- обновление Subscription.next_billing_at
"""
from __future__ import annotations

from datetime import timedelta, datetime
from typing import Optional

from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError

from apps.subscriptions.models import BillingSchedule, Subscription

from utils.enums import PeriodUnit
from utils.validators import validate_billing_schedule_params
from utils.date_calculator import get_tzinfo, add_months, clamp_day_to_month, next_week


def _next_for_day(dtime: datetime, interval: int) -> datetime:
    """
    Вычисляем следующую дату для "каждые N дней"
    """
    return dtime + timedelta(days=interval)


def _next_for_week(dtime: datetime, interval: int, anchor_weekday: int) -> datetime:
    """
    Вычисляем следующую дату для "каждые N недель" на конкретный день недели.
    """
    return next_week(dtime, anchor_weekday, interval)


def _next_for_month(dtime: datetime, interval: int, anchor_day: int) -> datetime:
    """
    Вычисляем следующую дату для "каждые N месяцев" на конкретное число.
    """
    day = clamp_day_to_month(dtime.year, dtime.month, anchor_day)
    res_dtime = dtime.replace(day=day)
    if res_dtime <= dtime:
        res_dtime = add_months(res_dtime, interval)
        day = clamp_day_to_month(res_dtime.year, res_dtime.month, anchor_day)
        res_dtime = res_dtime.replace(day=day)
    return res_dtime


def _next_for_year(dtime: datetime, interval: int) -> datetime:
    """
    Вычисляем следующую дату для "каждые N лет"
    """
    year = dtime.year + interval
    day = clamp_day_to_month(year, dtime.month, dtime.day)
    return dtime.replace(year=year, day=day)


@transaction.atomic
def recalculate_schedule_next_run(schedule: BillingSchedule, *, from_dt: datetime) -> BillingSchedule:
    """
    Пересчитывает schedule.next_run_at, учитывая timezone подписки.

    from_dt — “опорный момент”, от которого считаем следующий run.
    Обычно это timezone.now().
    """
    sub = schedule.subscription
    tzone = get_tzinfo(sub.billing_timezone)

    # Переводим опорный момент в локальную зону “подписки”
    local_dtime = timezone.localtime(from_dt, tzone)

    validate_billing_schedule_params(period_unit=schedule.period_unit,
                                     period_interval=schedule.period_interval,
                                     anchor_day=schedule.anchor_day,
                                     anchor_weekday=schedule.anchor_weekday,
                                     grace_days=schedule.grace_days)

    # Trial: если trial_ends_at позже from_dt, считаем от конца trial
    if schedule.trial_ends_at:
        local_trial = timezone.localtime(schedule.trial_ends_at, tzone)
        if local_trial > local_dtime:
            local_dtime = local_trial

    # Ищем следующую дату
    if schedule.period_unit == PeriodUnit.DAY:
        next_dtime = _next_for_day(local_dtime, schedule.period_interval)
    elif schedule.period_unit == PeriodUnit.WEEK:
        next_dtime = _next_for_week(local_dtime, schedule.period_interval, schedule.anchor_weekday or 0)
    elif schedule.period_unit == PeriodUnit.MONTH:
        next_dtime = _next_for_month(local_dtime, schedule.period_interval, schedule.anchor_day or 1)
    elif schedule.period_unit == PeriodUnit.YEAR:
        next_dtime = _next_for_year(local_dtime, schedule.period_interval)
    else:
        raise ValidationError(f"Период не найден: {schedule.period_unit}")

    # Возвращаем в UTC (для хранения)
    next_utc = next_dtime.astimezone(timezone.utc)
    schedule.next_run_at = next_utc
    schedule.save(update_fields=["next_run_at", "update_at"])
    return schedule


@transaction.atomic
def sync_subscription_next_billing(sub: Subscription) -> None:
    """
    Синхронизирует Subscription.next_billing_at из актуального BillingSchedule.next_run_at.
    """
    current = BillingSchedule.objects.filter(subscription=sub, is_current=True).order_by("-create_at").first()
    sub.next_billing_at = current.next_run_at if current else None
    sub.save(update_fields=["next_billing_at", "update_at"])