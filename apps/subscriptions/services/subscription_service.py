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

from apps.subscriptions.models import (BillingSchedule,
                                       PriceHistory,
                                       Subscription,
                                       VerifiedPrice,
                                       Provider,
                                       Category,)

from apps.subscriptions.services.billing_service import (get_current_schedule,
                                                         get_last_schedule,
                                                         close_current_schedule,
                                                         create_schedule_from_existing,
                                                         create_schedule_from_remaining_period,
                                                         recalculate_schedule_next_run,
                                                         sync_subscription_next_billing,)

from utils.enums import SubscriptionStatus, PriceHistorySource
from utils.validators import (validator_price_history_source,
                              validator_billing_schedule_params,
                              validator_timezone,
                              validator_subscription_status,
                              validator_subscription_status_change,)

#----------------------------------------------------------------------------------------------

@dataclass(frozen=True)
class PriceInput:
    """
    DTO для передачи цены
    """
    verified_price: Optional[VerifiedPrice] = None
    amount: Optional[Decimal] = None
    currency: Optional[str] = None
    effective_from: Optional[timezone.datetime] = None
    change_reason: Optional[str] = None
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

#----------------------------------------------------------------------------------------------

def _initial_subscription_create_status(*, started_at, now, trial_ends_at=None) -> SubscriptionStatus:
    """
    Определение начального статуса подписки
    """
    if trial_ends_at is not None and trial_ends_at >= now:
        return SubscriptionStatus.TRIAL

    if started_at is not None and started_at > now:
        return SubscriptionStatus.DELAYED

    return SubscriptionStatus.ACTIVE


def _initial_schedule_from_dt(*, initial_status: str, started_at, now):
    """
    Расчет начальной даты для формирования расписания
    """
    if initial_status == SubscriptionStatus.DELAYED:
        return started_at

    return now


def _get_price_subscription(sub: Subscription) -> PriceHistory:
    """
    Получение актуальной цены по подписке

    ! Возможна только 1 действующая цена с пустой effective_to
    """
    return PriceHistory.objects.filter(subscription=sub, effective_to__isnull=True).select_related('verified_price').first()  # First для подстраховки


def _set_billing_timezone_subscription(sub: Subscription, new_billing_timezone: str) -> bool:
    """
    Обновление временной зоны подписки и синхронизация расписания
    """
    if new_billing_timezone is None or new_billing_timezone == sub.billing_timezone:
        return False

    validator_timezone(new_billing_timezone)
    sub.billing_timezone = new_billing_timezone

    if sub.status == SubscriptionStatus.ACTIVE:
        schedule = get_current_schedule(sub)
        if schedule:
            recalculate_schedule_next_run(schedule, new_billing_timezone)
            sync_subscription_next_billing(sub)
    return True


def _build_pause_meta(*, subscription: Subscription, now) ->  dict:
    """
    Сборка JSON для Subscription.meta (связанных с PAUSE)
    """
    # Расчет остаточного периода до следующего списания в секундах
    remaining_billing_seconds = None
    if subscription.next_billing_at:
        delta = subscription.next_billing_at - now
        remaining_billing_seconds = max(0, int(delta.total_seconds()))
    return {
        "paused_at": now.isoformat(),
        "remaining_billing_seconds": remaining_billing_seconds,
    }


def _clear_subscription_meta_pause(meta: dict) -> dict:
    """
    Очистка полей Subscription.meta JSON связанных с PAUSE
    """
    meta["paused_at"] = None
    meta["remaining_billing_seconds"] = None
    return meta


def _status_transition_calculation(*, subscription: Subscription, status_new: str, started_at, now):
    """
    Доменная логика для расчёта нового состояния (статуса) Subscription.
    Возвращает dict с изменениями необходимыми для смены статуса.
    """
    trial_ends_at = getattr(subscription, "trial_ends_at", None)
    meta = dict(subscription.meta or {})

    result = {
        "status": subscription.status,
        "started_at": subscription.started_at,
        "ended_at": subscription.ended_at,
        "next_billing_at": subscription.next_billing_at,
        "meta": meta,
        "close_schedule": False,
        "resume_schedule": False,
        "recalculate_schedule": False,
    }

    if status_new == SubscriptionStatus.TRIAL:
        raise ValueError("TRIAL нельзя устанавливать через оркестратор статуса. "
                         "TRIAL допускается только при создании подписки.")

    elif status_new == SubscriptionStatus.DELAYED:
        result["status"] = SubscriptionStatus.DELAYED
        result["started_at"] = started_at
        result["ended_at"] = None
        result["next_billing_at"] = None
        result["resume_schedule"] = True
        _clear_subscription_meta_pause(meta)

    elif status_new == SubscriptionStatus.ACTIVE:
        result["status"] = SubscriptionStatus.ACTIVE
        result["ended_at"] = None
        if subscription.status in (SubscriptionStatus.PAUSED, SubscriptionStatus.CANCELED):
            result["resume_schedule"] = True
        elif subscription.status == SubscriptionStatus.EXPIRED:
            result["resume_schedule"] = True
            result["started_at"] = now
        elif subscription.status == SubscriptionStatus.DELAYED:
            # schedule уже есть → просто пересчитать
            result["recalculate_schedule"] = True
        _clear_subscription_meta_pause(meta)

    elif status_new == SubscriptionStatus.PAUSED:
        result["status"] = SubscriptionStatus.PAUSED
        result["ended_at"] = None
        result["next_billing_at"] = None
        result["close_schedule"] = True
        pause_meta = _build_pause_meta(subscription=subscription, now=now)
        meta.update(pause_meta)

    elif status_new == SubscriptionStatus.CANCELED:
        if subscription.next_billing_at:
            result["status"] = SubscriptionStatus.CANCELED
            result["ended_at"] = subscription.next_billing_at
        else:
            result["status"] = SubscriptionStatus.EXPIRED
            result["ended_at"] = now
        result["next_billing_at"] = None
        result["close_schedule"] = True
        _clear_subscription_meta_pause(meta)

    elif status_new == SubscriptionStatus.EXPIRED:
        result["status"] = SubscriptionStatus.EXPIRED
        result["ended_at"] = now
        result["next_billing_at"] = None
        result["close_schedule"] = True
        _clear_subscription_meta_pause(meta)

    # Валидация состояния
    validator_subscription_status(status=result["status"],
                                  started_at=result["started_at"],
                                  ended_at=result["ended_at"],
                                  trial_ends_at=trial_ends_at,
                                  now=now)

    return result

#----------------------------------------------------------------------------------------------

@transaction.atomic
def create_subscription_with_defaults(*, user,
                                         title: str,
                                         description: Optional[str] = None,
                                         provider: Optional[Provider] = None,
                                         category: Optional[Category] = None,
                                         started_at = None,
                                         ended_at = None,
                                         billing_timezone: Optional[str] = None,
                                         payment_method_label: Optional[str] = None,
                                         owner_note: Optional[str] = None,
                                         is_shared: bool = False,
                                         now = None,
                                         price: PriceInput,
                                         schedule: ScheduleInput) -> Subscription:
    """
    Создание подписки со всеми связанными сущностями:
    - Subscription
    - PriceHistory (текущая цена)
    - BillingSchedule (актуальный график)

    Определяет начальный статус.
    Рассчитывает next_run_at и синхронизирует Subscription.next_billing_at.

    Это "правильная" точка входа для создания новой подписки в домене.
    """
    now = now or timezone.now()

    # Проверка billing_timezone, при отсутствии берем с пользователя или UTC
    if billing_timezone is not None:
        validator_timezone(value=billing_timezone)
    else:
        billing_timezone = getattr(user, 'timezone', 'UTC')

    # Задаем по умолчанию now
    started_at = now if started_at is None else started_at

    # Определение начального статуса
    initial_status = _initial_subscription_create_status(started_at=started_at, now=now, trial_ends_at=schedule.trial_ends_at)

    # Валидация статуса
    validator_subscription_status(status=initial_status,
                                  started_at=started_at,
                                  ended_at=ended_at,
                                  trial_ends_at=schedule.trial_ends_at,
                                  now=now)

    # Инициализация JSON параметров для подписки
    initial_meta = {"paused_at": None,
                    "remaining_billing_seconds": None,}

    # Момент вступления цены в силу
    effective_from = price.effective_from or now

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
                                      status=initial_status,
                                      started_at=started_at,
                                      ended_at=ended_at,
                                      payment_method_label=payment_method_label,
                                      owner_note=owner_note,
                                      is_shared=is_shared,
                                      current_price_amount=amount,
                                      current_price_currency=current,
                                      billing_timezone=billing_timezone,
                                      meta = initial_meta,)

    if price.source == PriceHistorySource.VERIFIED:
        PriceHistory.objects.create(subscription=sub,
                                    verified_price=price.verified_price,
                                    effective_from=effective_from,
                                    change_reason=price.change_reason,
                                    source=price.source)
    elif price.source == PriceHistorySource.MANUAL:
        PriceHistory.objects.create(subscription=sub,
                                    amount=price.amount,
                                    currency=price.currency,
                                    effective_from=effective_from,
                                    change_reason=price.change_reason,
                                    source=price.source)

    validator_billing_schedule_params(period_unit=schedule.period_unit,
                                     period_interval=schedule.period_interval,
                                     anchor_day=schedule.anchor_day,
                                     anchor_weekday=schedule.anchor_weekday,
                                     grace_days=schedule.grace_days)

    # Начальная точка расчета расписания (в основном now, но для DELAYED started_at)
    schedule_from_dt = _initial_schedule_from_dt(initial_status=initial_status, started_at=started_at, now=now)

    sched = BillingSchedule.objects.create(subscription=sub,
                                           period_unit=schedule.period_unit,
                                           period_interval=schedule.period_interval,
                                           anchor_day=schedule.anchor_day,
                                           anchor_weekday=schedule.anchor_weekday,
                                           trial_ends_at=schedule.trial_ends_at,
                                           grace_days=schedule.grace_days,
                                           # Для создания ставим next_run_at = schedule_from_dt, сразу же пересчитаем корректно ниже
                                           next_run_at=schedule_from_dt,
                                           is_current=True)

    recalculate_schedule_next_run(sched, from_dt=schedule_from_dt)
    sync_subscription_next_billing(sub)
    return sub


@transaction.atomic
def update_subscription_data(*, subscription: Subscription,
                                title: str,
                                description: Optional[str] = None,
                                category: Optional[Category] = None,
                                billing_timezone: Optional[str] = None,
                                payment_method_label: Optional[str] = None,
                                owner_note: Optional[str] = None,
                                is_shared: bool = None) -> Subscription:
    """
    Обновление простых полей подписки

    ! При изменении billing_timezone происходит обновление next_run_at и синхронизация Subscription.next_billing_at.
    """
    # Блочим subscription чтобы не получить конкурентного обновления
    sub_lock = Subscription.objects.select_for_update().get(pk=subscription.pk)

    update_fields = []

    # Обновление простых полей
    if title:
        sub_lock.title = title
        update_fields.append('title')

    if description is not None:
        sub_lock.description = description
        update_fields.append('description')

    if payment_method_label is not None:
        sub_lock.payment_method_label = payment_method_label
        update_fields.append('payment_method_label')

    if owner_note is not None:
        sub_lock.owner_note = owner_note
        update_fields.append('owner_note')

    if sub_lock.is_shared is not None:
        sub_lock.is_shared = is_shared
        update_fields.append('is_shared')

    if category is not None:
        sub_lock.category = category
        update_fields.append('category')

    if billing_timezone is not None:
        if _set_billing_timezone_subscription(sub_lock, billing_timezone):
            update_fields.append('billing_timezone')

    if update_fields:
        update_fields.append('update_at')
        sub_lock.save(update_fields=update_fields)

    return sub_lock


@transaction.atomic
def set_subscription_price(*, subscription: Subscription,
                              verified_price: Optional[VerifiedPrice] = None,
                              amount: Optional[Decimal] = None,
                              currency: Optional[str] = None,
                              effective_from = None,
                              change_reason: Optional[str] = None,
                              now = None,
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
    now = now or timezone.now()
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
                                                change_reason=change_reason,
                                                source=source)
        sub_lock.current_price_amount = verified_price.amount
        sub_lock.current_price_currency = verified_price.currency

    else: # Manual
        new_price = PriceHistory.objects.create(subscription=subscription,
                                                amount=amount,
                                                currency=currency,
                                                effective_from=effective_from,
                                                change_reason=change_reason,
                                                source=source)
        sub_lock.current_price_amount = amount
        sub_lock.current_price_currency = currency

    sub_lock.save(update_fields=["current_price_amount", "current_price_currency", "update_at"])

    return new_price


@transaction.atomic
def set_subscription_status(*, subscription: Subscription,
                               status_new: str,
                               started_at=None,
                               now=None) -> Subscription:
    """
    Сервис для смены статуса подписки.
    Используется во всех сценариях:
    - API
    - Tasks
    -Внутренние сервисы

    ! Смена статуса должна проходить исключительно через этот сервис
    Это основная точка входа для изменения статуса (состояния) Subscription в домене.
    """
    now = now or timezone.now()

    # Блокировка объекта Subscription
    subscription = Subscription.objects.select_for_update().get(pk=subscription.pk)

    status_old = subscription.status

    # Проверка возможности смены статуса
    validator_subscription_status_change(status_current=subscription.status, status_new=status_new)

    # Сбор перечня изменений
    changes = _status_transition_calculation(subscription=subscription, status_new=status_new,
                                             started_at=started_at, now=now)

    # Закрытие расписания
    if changes["close_schedule"]:
        close_current_schedule(sub=subscription)

    # Возможно либо создание, либо пересчет
    # Создание нового расписания
    if changes["resume_schedule"]:
        meta = subscription.meta or {}
        remaining = meta.get("remaining_billing_seconds")
        if remaining is not None:
            new_schedule = create_schedule_from_remaining_period(sub=subscription,
                                                                 remaining_billing_seconds=remaining,
                                                                 from_dt=now)
        else:
            new_schedule = create_schedule_from_existing(sub=subscription, from_dt=now)
        changes["next_billing_at"] = new_schedule.next_run_at

    # Пересчет существующего расписания
    elif changes["recalculate_schedule"]:
        schedule = get_current_schedule(subscription)
        if schedule:
            recalculate_schedule_next_run(schedule, from_dt=now)
            changes["next_billing_at"] = schedule.next_run_at

    update_fields = []

    if subscription.status != changes["status"]:
        subscription.status = changes["status"]
        update_fields.append("status")

    if subscription.started_at != changes["started_at"]:
        subscription.started_at = changes["started_at"]
        update_fields.append("started_at")

    if subscription.ended_at != changes["ended_at"]:
        subscription.ended_at = changes["ended_at"]
        update_fields.append("ended_at")

    if subscription.next_billing_at != changes["next_billing_at"]:
        subscription.next_billing_at = changes["next_billing_at"]
        update_fields.append("next_billing_at")

    if subscription.meta != changes["meta"]:
        subscription.meta = changes["meta"]
        update_fields.append("meta")

    if update_fields:
        update_fields.append("update_at")
        subscription.save(update_fields=update_fields)

    return subscription