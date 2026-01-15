"""
Subscription service

Функционал:
- создание подписки с дефолтным расписанием/ценой
- смена провайдера/подписки
- операции обновления данных
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

from django.db import transaction
from django.utils import timezone

from apps.subscriptions.models import BillingSchedule, PriceHistory, Subscription
from apps.subscriptions.services.billing_service import (recalculate_schedule_next_run,
    sync_subscription_next_billing,
    validate_billing_schedule_params,
)

from utils.enums import Status, Source


@dataclass(frozen=True)
class PriceInput:
    """
    DTO для передачи цены
    """
    amount: Decimal
    currency: str
    effective_from: Optional[timezone.datetime] = None
    reason: Optional[str] = None
    source: str = Source.MANUAL


@dataclass(frozen=True)
class ScheduleInput:
    """
    DTO для передачи параметров расписания
    """
    period_unit: str
    period_interval: int = 1
    anchor_day: Optional[int] = None
    anchor_weekday: Optional[int] = None
    trial_ends_at: Optional[timezone.datetime] = None
    grace_days: int = 0
    billing_timezone: Optional[str] = None


@transaction.atomic
def create_subscription_with_defaults(*, user, title: str, description: Optional[str] = None,
                                         provider=None, category=None, status: str = Status.ACTIVE,
                                         started_at=None, ended_at=None, payment_method_label: Optional[str] = None,
                                         owner_note: Optional[str] = None, is_shared: bool = False,
                                         price: PriceInput, schedule: ScheduleInput) -> Subscription:
    """
    Создание подписки со всеми связанными сущностями:
    - Subscription
    - PriceHistory (текущая цена)
    - BillingSchedule (актуальный график)

    Рассчитывает next_run_at и синхронизирует Subscription.next_billing_at.

    Это "правильная" точка входа для создания подписки в домене.
    """
    # Момент вступления цены в силу
    effective_from = price.effective_from or timezone.now()

    sub = Subscription.objects.create(user=user,
                                      provider=provider,
                                      category=category,
                                      title=title,
                                      description=description,
                                      status=status,
                                      started_at=started_at,
                                      ended_at=ended_at,
                                      payment_method_label=payment_method_label,
                                      owner_note=owner_note,
                                      is_shared=is_shared,
                                      current_price_amount=price.amount,
                                      current_price_currency=price.currency,
                                      billing_timezone=schedule.billing_timezone)

    PriceHistory.objects.create(subscription=sub,
                                amount=price.amount,
                                currency=price.currency,
                                effective_from=effective_from,
                                change_reason=price.reason,
                                source=price.source)

    validate_billing_schedule_params(period_unit=schedule.period_unit,
                                     period_interval=schedule.period_interval,
                                     anchor_day=schedule.anchor_day,
                                     anchor_weekday=schedule.anchor_weekday,
                                     grace_days=schedule.grace_days)

    sched = BillingSchedule.objects.create(subscription=sub,
                                           period_unit=schedule.period_unit,
                                           period_interval=schedule.period_interval,
                                           anchor_day=schedule.anchor_day,
                                           anchor_weekday=schedule.anchor_weekday,
                                           trial_ends_at=schedule.trial_ends_at,
                                           grace_days=schedule.grace_days,
                                           # временно ставим next_run_at = now, сразу же пересчитаем корректно ниже
                                           next_run_at=timezone.now(),
                                           is_current=True)

    recalculate_schedule_next_run(sched, dtime=timezone.now())
    sync_subscription_next_billing(sub)
    return sub


@transaction.atomic
def set_subscription_price(*, subscription: Subscription, amount: Decimal, currency: str,
                           effective_from: Optional[timezone.datetime] = None, reason: Optional[str] = None,
                           source: str = Source.MANUAL) -> PriceHistory:
    """
    Меняет текущую цену подписки:
    - обновляет Subscription.current_price_*
    - закрывает предыдущую активную запись PriceHistory (effective_to)
    - создаёт новую PriceHistory

    Правило: в любой момент должна быть “текущая” запись PriceHistory с effective_to = NULL.

    Это "правильная" точка входа для изменения цены в домене.
    """
    # Момент вступления цены в силу
    effective_from = effective_from or timezone.now()

    # Текущая активная цена (если есть)
    prev = PriceHistory.objects.select_for_update().filter(subscription=subscription, effective_to__isnull=True).order_by("-effective_from").first()

    if prev and prev.effective_from < effective_from:
        # Закрываем предыдущую “текущую” запись
        prev.effective_to = effective_from
        prev.save(update_fields=["effective_to"])
    elif prev and prev.effective_from >= effective_from:
        raise ValueError("Значение effective_from должно быть больше текущей активной цены effective_from.")

    entry = PriceHistory.objects.create(subscription=subscription,
                                        amount=amount,
                                        currency=currency,
                                        effective_from=effective_from,
                                        change_reason=reason,
                                        source=source)

    subscription.current_price_amount = amount
    subscription.current_price_currency = currency
    subscription.save(update_fields=["current_price_amount", "current_price_currency", "update_at"])

    return entry