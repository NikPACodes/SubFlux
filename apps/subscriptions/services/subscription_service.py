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

from apps.subscriptions.models import BillingSchedule, PriceHistory, Subscription, VerifiedPrice
from apps.subscriptions.services.billing_service import (recalculate_schedule_next_run,
                                                         sync_subscription_next_billing)

from utils.enums import SubscriptionStatus, PriceHistorySource
from utils.validators import validator_price_history_source, validate_billing_schedule_params


@dataclass(frozen=True)
class PriceInput:
    """
    DTO для передачи цены
    """
    verified_price: Optional[VerifiedPrice] = None
    amount: Optional[Decimal] = None
    currency: Optional[str] = None
    effective_from: Optional[timezone.datetime] = None
    reason: Optional[str] = None
    source: str = PriceHistorySource.MANUAL


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
                                         provider=None, category=None, status: str = SubscriptionStatus.ACTIVE,
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

    # Проверка корректности режимов manual/verified
    validator_price_history_source(source=price.source,
                                   verified_price=price.verified_price,
                                   amount=price.amount,
                                   currency=price.currency)

    if price.source == PriceHistorySource.VERIFIED:
        amount = price.verified_price.amount
        current = price.verified_price.currency
    else: # Manual
        amount = price.amount
        current = price.currency

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
                                      current_price_amount=amount,
                                      current_price_currency=current,
                                      billing_timezone=schedule.billing_timezone)


    if price.source == PriceHistorySource.VERIFIED:
        PriceHistory.objects.create(subscription=sub,
                                    verified_price=price.verified_price,
                                    effective_from=effective_from,
                                    change_reason=price.reason,
                                    source=price.source)
    elif price.source == PriceHistorySource.MANUAL:
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

    recalculate_schedule_next_run(sched, from_dt=timezone.now())
    sync_subscription_next_billing(sub)
    return sub


@transaction.atomic
def set_subscription_price(*, subscription: Subscription, verified_price: Optional[VerifiedPrice] = None,
                           amount: Optional[Decimal] = None, currency: Optional[str] = None,
                           effective_from: Optional[timezone.datetime] = None, reason: Optional[str] = None,
                           source: str = PriceHistorySource.MANUAL) -> PriceHistory:
    """
    Меняет текущую цену подписки:
    - обновляет Subscription.current_price_*
    - закрывает предыдущую активную запись PriceHistory (effective_to)
    - создаёт новую PriceHistory

    Правило: в любой момент должна быть “текущая” запись PriceHistory с effective_to = NULL.

    Это "правильная" точка входа для изменения цены в домене.
    """
    # Проверка корректности режимов manual/verified
    validator_price_history_source(source=source,
                                   verified_price=verified_price,
                                   amount=amount,
                                   currency=currency)

    # Момент вступления цены в силу
    now = timezone.now()
    if effective_from and effective_from > now:
        raise ValueError("Значение effective_from в будущем не поддерживается.")
    elif not effective_from:
        effective_from = now

    # Блочим subscription чтобы не получить конкурентного обновления
    sub_lock = Subscription.objects.select_for_update().get(pk=subscription.pk)

    # Текущая активная цена (если есть)
    # ! Может существовать только одна активная PriceHistory к конкретной Subscription
    prev_price = PriceHistory.objects.select_for_update().filter(subscription=subscription, effective_to__isnull=True).first()

    if prev_price and prev_price.effective_from < effective_from:
        # Закрываем предыдущую “текущую” запись
        prev_price.effective_to = effective_from
        prev_price.save(update_fields=["effective_to"])
    elif prev_price and prev_price.effective_from >= effective_from:
        raise ValueError("Значение effective_from должно быть больше текущей активной цены effective_from.")

    if source == PriceHistorySource.VERIFIED:
        new_price = PriceHistory.objects.create(subscription=subscription,
                                                verified_price=verified_price,
                                                effective_from=effective_from,
                                                change_reason=reason,
                                                source=source)
        sub_lock.current_price_amount = verified_price.amount
        sub_lock.current_price_currency = verified_price.currency

    else: # Manual
        new_price = PriceHistory.objects.create(subscription=subscription,
                                                amount=amount,
                                                currency=currency,
                                                effective_from=effective_from,
                                                change_reason=reason,
                                                source=source)
        sub_lock.current_price_amount = amount
        sub_lock.current_price_currency = currency

    sub_lock.save(update_fields=["current_price_amount", "current_price_currency", "update_at"])

    return new_price