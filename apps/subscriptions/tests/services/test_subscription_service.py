import pytest
from decimal import Decimal
from datetime import timedelta, datetime
from zoneinfo import ZoneInfo
from django.utils import timezone
from django.core.validators import ValidationError
from apps.subscriptions.models import PriceHistory
from apps.subscriptions.services.subscription_service import (PriceInput, ScheduleInput,
                                                              create_subscription_with_defaults,
                                                              update_subscription_data,
                                                              set_subscription_price)
from utils.date_calculator import get_tzinfo, next_week
from utils.enums import SubscriptionStatus, PriceHistorySource, PeriodUnit


#--------------------------- Тесты сервиса по созданию подписки ---------------------------
@pytest.mark.django_db
def test_service_create_subscription_manual_full(subscription_data_default,
                                                 user_default, provider_default, category_default):
    """
    Проверка сервиса по созданию Subscription, PriceHistory, BillingSchedules в Manual режиме (create_subscription_with_defaults):
    - Subscription создается
    - current_price_amount и current_price_currency корректно записаны в Subscription
    - next_billing_at успешно посчитан и записан в Subscription
    - PriceHistory создается
    - Данные PriceInput корректно записаны в PriceHistory
    - BillingSchedules создается
    - Данные ScheduleInput корректно записаны в BillingSchedules
    - next_run_at успешно посчитан и записан в BillingSchedules
    """
    test_u = user_default
    test_p = provider_default
    test_cat = category_default

    test_price_manual = PriceInput(amount=Decimal('20.10'),
                                   currency="USD",
                                   source=PriceHistorySource.MANUAL)

    test_schedule = ScheduleInput(period_unit=PeriodUnit.WEEK,
                                  period_interval=1,
                                  anchor_weekday=1)

    test_service_subscription_manual = create_subscription_with_defaults(user=test_u,
                                                                         title=subscription_data_default['title'],
                                                                         provider=test_p,
                                                                         category=test_cat,
                                                                         started_at=timezone.now(),
                                                                         ended_at=None,
                                                                         billing_timezone="Europe/Moscow",
                                                                         payment_method_label="VISA",
                                                                         owner_note="Доп. заметки",
                                                                         is_shared=False,
                                                                         price=test_price_manual,
                                                                         schedule=test_schedule)
    # Тест Subscription
    assert test_service_subscription_manual.id is not None
    assert test_service_subscription_manual.next_billing_at is not None
    assert test_service_subscription_manual.current_price_amount == test_price_manual.amount
    assert test_service_subscription_manual.current_price_currency == test_price_manual.currency

    test_price_history = test_service_subscription_manual.price_history.first()

    # Тест PriceHistory
    assert test_price_history.id is not None
    assert test_price_history.source == test_price_manual.source
    assert test_price_history.amount == test_price_manual.amount
    assert test_price_history.currency == test_price_manual.currency
    assert test_price_history.verified_price is None
    assert test_price_history.effective_to is None

    test_billing_schedules = test_service_subscription_manual.billing_schedules.first()

    tzone = get_tzinfo(test_service_subscription_manual.billing_timezone)  # Получение тайм зоны подписки
    local_dtime = timezone.localtime(timezone.now(), tzone)                # Перевод в локальное время
    test_next_week = next_week(dtime=local_dtime,                          # Расчет следующей даты
                               weekday=test_schedule.anchor_weekday,
                               interval=test_schedule.period_interval)
    test_next_run_at = test_next_week.astimezone(timezone.UTC)              # Получаем UTC (для хранения)

    # Тест BillingSchedules
    assert test_billing_schedules.id is not None
    assert test_billing_schedules.period_unit == test_schedule.period_unit
    assert test_billing_schedules.period_interval == test_schedule.period_interval
    assert test_billing_schedules.anchor_weekday == test_schedule.anchor_weekday
    assert test_billing_schedules.next_run_at.date() == test_next_run_at.date()
    assert test_billing_schedules.next_run_at == test_service_subscription_manual.next_billing_at
    assert test_billing_schedules.is_current is True


@pytest.mark.django_db
def test_service_create_subscription_verified_full(subscription_data_default,
                                                   user_default, provider_default, category_default,
                                                   verified_price_data_default, verified_price_factory):
    """
    Проверка сервиса по созданию Subscription, PriceHistory, BillingSchedules в Verified режиме (create_subscription_with_defaults):
    - Subscription создается
    - current_price_amount и current_price_currency корректно записаны в Subscription
    - next_billing_at успешно посчитан и записан в Subscription
    - PriceHistory создается
    - Данные PriceInput (source, amount и currency) корректно записаны в PriceHistory
    - BillingSchedules создается
    - Данные ScheduleInput (period_unit, period_interval и anchor_weekday) корректно записаны в BillingSchedules
    - next_run_at успешно посчитан и записан в BillingSchedules
    """
    test_u = user_default
    test_p = provider_default
    test_cat = category_default
    test_vp = verified_price_factory(provider=test_p, plan_name=verified_price_data_default["plan_name"],
                                     amount=verified_price_data_default["amount"])
    test_price_verified = PriceInput(verified_price=test_vp,
                                     source=PriceHistorySource.VERIFIED)
    test_schedule = ScheduleInput(period_unit=PeriodUnit.WEEK,
                                  period_interval=1,
                                  anchor_weekday=1)

    test_service_subscription_verified = create_subscription_with_defaults(user=test_u,
                                                                           title="Тестовая подписка 1",
                                                                           provider=test_p,
                                                                           category=test_cat,
                                                                           started_at=timezone.now(),
                                                                           ended_at=None,
                                                                           billing_timezone="Europe/Moscow",
                                                                           payment_method_label="VISA",
                                                                           owner_note="Доп. заметки",
                                                                           is_shared=False,
                                                                           price=test_price_verified,
                                                                           schedule=test_schedule)

    # Тест Subscription
    assert test_service_subscription_verified.id is not None
    assert test_service_subscription_verified.next_billing_at is not None
    assert test_service_subscription_verified.current_price_amount == test_vp.amount
    assert test_service_subscription_verified.current_price_currency == test_vp.currency

    test_price_history = test_service_subscription_verified.price_history.first()

    # Тест PriceHistory
    assert test_price_history.id is not None
    assert test_price_history.source == test_price_verified.source
    assert test_price_history.verified_price.amount == test_vp.amount
    assert test_price_history.verified_price.currency == test_vp.currency
    assert all(ch is None for ch in (test_price_history.amount, test_price_history.currency))
    assert test_price_history.effective_to is None

    test_billing_schedules = test_service_subscription_verified.billing_schedules.first()

    tzone = get_tzinfo(test_service_subscription_verified.billing_timezone)  # Получение тайм зоны подписки
    local_dtime = timezone.localtime(timezone.now(), tzone)                # Перевод в локальное время
    test_next_week = next_week(dtime=local_dtime,                        # Расчет следующей даты
                                 weekday=test_schedule.anchor_weekday,
                                 interval=test_schedule.period_interval)
    test_next_run_at = test_next_week.astimezone(timezone.UTC)              # Получаем UTC (для хранения)

    # Тест BillingSchedules
    assert test_billing_schedules.id is not None
    assert test_billing_schedules.period_unit == test_schedule.period_unit
    assert test_billing_schedules.period_interval == test_schedule.period_interval
    assert test_billing_schedules.anchor_weekday == test_schedule.anchor_weekday
    assert test_billing_schedules.next_run_at.date() == test_next_run_at.date()
    assert test_billing_schedules.next_run_at == test_service_subscription_verified.next_billing_at
    assert test_billing_schedules.is_current is True


@pytest.mark.django_db
def test_service_create_trial_subscription(subscription_data_default, user_default):
    """
    Проверка сервиса по созданию Subscription с начальным TRIAL статусом
    - Subscription создана со статусом TRIAL
    - trial_ends_at проставлен
    - next_run_at пересчитан с учетом trial периода
    """
    utc_tz = ZoneInfo('UTC')
    now =datetime(2026, 1, 3, 0, 0, tzinfo=utc_tz)
    started_at = datetime(2026, 1, 1, 0, 0, tzinfo=utc_tz)
    trial_ends_at = datetime(2026, 1, 5, 0, 0, tzinfo=utc_tz)
    recalc_next_billing_at = datetime(2026, 1, 12, 0, 0, tzinfo=utc_tz)

    test_u = user_default
    test_price_manual = PriceInput(amount=Decimal('20.10'), currency="USD", source=PriceHistorySource.MANUAL)
    test_schedule = ScheduleInput(period_unit=PeriodUnit.WEEK, period_interval=1, anchor_weekday=0,
                                  trial_ends_at=trial_ends_at)

    test_service_subscription_trial = create_subscription_with_defaults(user=test_u,
                                                                        title=subscription_data_default['title'],
                                                                        started_at=started_at,
                                                                        billing_timezone=subscription_data_default['billing_timezone'],
                                                                        price=test_price_manual,
                                                                        schedule=test_schedule,
                                                                        now=now)
    test_billing_schedules = test_service_subscription_trial.billing_schedules.filter(is_current=True).first()
    assert test_service_subscription_trial.status == SubscriptionStatus.TRIAL
    assert test_service_subscription_trial.next_billing_at == recalc_next_billing_at
    assert test_billing_schedules.trial_ends_at == trial_ends_at
    assert test_billing_schedules.next_run_at == recalc_next_billing_at

@pytest.mark.django_db
def test_service_create_delayed_subscription(subscription_data_default, user_default):
    """
    Проверка сервиса по созданию Subscription с начальным DELAYED статусом
    - Subscription создана со статусом DELAYED
    - Subscription.started_at > now
    - billing_schedules создан
    - next_run_at пересчитан с учетом DELAYED
    - проверка задания начального billing_timezone
    """
    utc_tz = ZoneInfo('UTC')
    now =datetime(2026, 1, 1, 0, 0, tzinfo=utc_tz)
    started_at = datetime(2026, 1, 5, 0, 0, tzinfo=utc_tz)
    recalc_next_billing_at = datetime(2026, 1, 12, 0, 0, tzinfo=utc_tz)

    test_u = user_default
    test_price_manual = PriceInput(amount=Decimal('20.10'), currency="USD", source=PriceHistorySource.MANUAL)
    test_schedule = ScheduleInput(period_unit=PeriodUnit.WEEK, period_interval=1, anchor_weekday=0)
    test_service_subscription_delayed = create_subscription_with_defaults(user=test_u,
                                                                          title=subscription_data_default['title'],
                                                                          started_at=started_at,
                                                                          billing_timezone=None,
                                                                          price=test_price_manual,
                                                                          schedule=test_schedule,
                                                                          now=now)
    test_billing_schedules = test_service_subscription_delayed.billing_schedules.filter(is_current=True).first()
    assert test_service_subscription_delayed.status == SubscriptionStatus.DELAYED
    assert test_service_subscription_delayed.started_at > now
    assert test_service_subscription_delayed.next_billing_at == recalc_next_billing_at
    assert test_billing_schedules.next_run_at == recalc_next_billing_at
    assert test_service_subscription_delayed.billing_timezone == "UTC"


@pytest.mark.django_db
def test_service_create_subscription_raises_verified_or_manual(subscription_data_default,
                                                               user_default, provider_default,
                                                               verified_price_data_default, verified_price_factory):
    """
    Нельзя заполнять одновременно поля verified_price, amount, currency в PriceInput
    - Для Verified -> Заполнено verified_price. Пустые amount и currency.
    - Для Manual -> Заполнены amount и currency. Пустое verified_price.
    """
    test_u = user_default
    test_p = provider_default
    test_vp = verified_price_factory(provider=test_p, plan_name=verified_price_data_default["plan_name"],
                                     amount=verified_price_data_default["amount"])
    test_price_verified = PriceInput(verified_price=test_vp,
                                     amount=Decimal('20.10'),
                                     currency="USD",
                                     source=PriceHistorySource.VERIFIED)

    test_schedule = ScheduleInput(period_unit=PeriodUnit.WEEK, period_interval=1, anchor_weekday=1)

    with pytest.raises(ValidationError):
        create_subscription_with_defaults(user=test_u, title="Тестовая подписка 1", provider=test_p,
                                          price=test_price_verified, schedule=test_schedule)


@pytest.mark.django_db
def test_service_create_subscription_raises_anchor(user_default):
    """
    Для ScheduleInput обязательно заполнение anchor_* для недели и месяца
    - Week -> anchor_weekday
    - Month -> anchor_day
    """
    test_u = user_default
    test_price = PriceInput(amount=Decimal('20.10'), currency="USD", source=PriceHistorySource.MANUAL)
    test_schedule = ScheduleInput(period_unit=PeriodUnit.WEEK)

    with pytest.raises(ValidationError):
        create_subscription_with_defaults(user=test_u, title="Тестовая подписка 1",
                                          price=test_price, schedule=test_schedule)


#--------------------------- Тесты сервиса по обновлению простых полей ---------------------------
@pytest.mark.django_db
def test_service_subscription_update_fields(user_default, category_factory):  #
    """
    Проверка обновления простых полей подписки
    - Простые поля успешно сохраняются
    - При изменении billing_timezone пересчитывается next_run_at и синхронизируется Subscription.next_billing_at.
    """
    test_u = user_default
    test_price_manual = PriceInput(amount=Decimal('25.10'), currency="USD", source=PriceHistorySource.MANUAL)
    test_schedule = ScheduleInput(period_unit=PeriodUnit.WEEK, period_interval=1, anchor_weekday=0)

    test_cat1 = category_factory(name="Категория1", slug="Cat1", sort_order=0)
    test_cat2 = category_factory(name="Категория2", slug="Cat2", sort_order=0)


    test_sub = create_subscription_with_defaults(user=test_u,
                                                 title="Тест обновления",
                                                 description="Описание",
                                                 category=test_cat1,
                                                 billing_timezone="Asia/Yekaterinburg",
                                                 payment_method_label="VISA",
                                                 owner_note="Заметка владельца",
                                                 is_shared=True,
                                                 price=test_price_manual,
                                                 schedule=test_schedule)
    assert test_sub.id is not None

    test_sub_update = update_subscription_data(subscription=test_sub,
                                               title="Обновленный заголовок",
                                               description="Обновленное расписание",
                                               category=test_cat2,
                                               billing_timezone="America/Los_Angeles",
                                               payment_method_label="Новый метод МИР",
                                               owner_note="Обновленная заметка",
                                               is_shared=False)

    assert test_sub.id == test_sub_update.id
    assert test_sub.title != test_sub_update.title
    assert test_sub.category != test_sub_update.category
    assert test_sub.payment_method_label != test_sub_update.payment_method_label
    assert test_sub.owner_note != test_sub_update.owner_note
    assert test_sub.is_shared != test_sub_update.is_shared
    assert test_sub.billing_timezone != test_sub_update.billing_timezone
    assert test_sub.next_billing_at != test_sub_update.next_billing_at


#--------------------------- Тесты сервиса по изменению цены ---------------------------
@pytest.mark.django_db
def test_service_set_price_manual_closes_previous(subscription_data_default, user_default):
    """
    Проверка сервиса по обновлению цены в Manual-режиме (set_subscription_price)
    - Создана новая активная PriceHistory с новыми данными
    - Предыдущая PriceHistory успешно закрыта (effective_to)
    - Поля Subscription.current_price_* успешно обновлены
    """
    # Создаем для Subscription + PriceHistory + BillingSchedule
    test_u = user_default
    test_price_manual = PriceInput(amount=Decimal('25.10'), currency="USD", source=PriceHistorySource.MANUAL)
    test_schedule = ScheduleInput(period_unit=PeriodUnit.WEEK, period_interval=1, anchor_weekday=1)
    test_sub_manual = create_subscription_with_defaults(user=test_u, title=subscription_data_default['title'],
                                                        price=test_price_manual, schedule=test_schedule)
    test_prev_price = test_sub_manual.price_history.first()

    # Обновление цены (закрытие старой цены и открытия новой)
    test_new_price = set_subscription_price(subscription=test_sub_manual,
                                            amount=Decimal('100.50'),
                                            currency="RUB",
                                            effective_from=timezone.now(),
                                            change_reason="Тестовое обновление цены",
                                            source=PriceHistorySource.MANUAL)

    test_prev_price_update = PriceHistory.objects.get(pk=test_prev_price.pk)
    test_sub_manual_updated = test_prev_price_update.subscription

    assert test_new_price.id != test_prev_price.id
    assert test_new_price.amount == Decimal('100.50')
    assert test_new_price.currency == "RUB"

    assert test_prev_price.effective_to is None
    assert test_prev_price_update.effective_to == test_new_price.effective_from

    assert test_sub_manual_updated.current_price_amount == Decimal('100.50')
    assert test_sub_manual_updated.current_price_currency == "RUB"


@pytest.mark.django_db
def test_service_set_price_verified_closes_previous(subscription_data_default,
                                                    user_default, provider_default,
                                                    verified_price_data_default, verified_price_factory):
    """
    Проверка сервиса по обновлению цены в Verified-режиме (set_subscription_price)
    - Создана новая активная PriceHistory с новыми данными
    - Предыдущая PriceHistory успешно закрыта (effective_to)
    - Поля Subscription.current_price_* успешно обновлены
    """
    # Создаем для Subscription + PriceHistory + BillingSchedule
    test_u = user_default
    test_p = provider_default
    test_vp = verified_price_factory(provider=test_p, plan_name=verified_price_data_default["plan_name"],
                                     amount=verified_price_data_default["amount"])
    test_price_verified = PriceInput(verified_price=test_vp, source=PriceHistorySource.VERIFIED)
    test_schedule = ScheduleInput(period_unit=PeriodUnit.WEEK, period_interval=1, anchor_weekday=1)
    test_sub_verified = create_subscription_with_defaults(user=test_u, title=subscription_data_default['title'],
                                                          provider=test_p, price=test_price_verified,
                                                          schedule=test_schedule)
    test_prev_price = test_sub_verified.price_history.first()

    test_vp_new = verified_price_factory(provider=test_p, plan_name=verified_price_data_default["plan_name"],
                                         amount=Decimal('100.50'), currency="RUB")

    # Обновление цены (закрытие старой цены и открытия новой)
    test_new_price = set_subscription_price(subscription=test_sub_verified,
                                            verified_price=test_vp_new,
                                            effective_from=timezone.now(),
                                            change_reason="Тестовое обновление цены",
                                            source=PriceHistorySource.VERIFIED)

    test_prev_price_update = PriceHistory.objects.get(pk=test_prev_price.pk)
    test_sub_manual_updated = test_prev_price_update.subscription

    assert test_new_price.id != test_prev_price.id
    assert test_new_price.verified_price.amount == Decimal('100.50')
    assert test_new_price.verified_price.currency == "RUB"

    assert test_prev_price.effective_to is None
    assert test_prev_price_update.effective_to == test_new_price.effective_from

    assert test_sub_manual_updated.current_price_amount == Decimal('100.50')
    assert test_sub_manual_updated.current_price_currency == "RUB"


@pytest.mark.django_db
@pytest.mark.parametrize("effective_from",
                        [ pytest.param(lambda now: now + timedelta(days=10), id="future"),
                          pytest.param(lambda now: now - timedelta(days=10), id="past")])
def test_service_set_price_raises_effective_from(subscription_data_default, user_default, effective_from):
    """
    Проверка effective_from
    - обновления цены в будущем (effective_from больше текущей даты/времени)
    - обновления цены в прошлом (effective_from меньше текущей активной цены effective_from)
    """
    # Создаем для Subscription + PriceHistory + BillingSchedule
    test_price_manual = PriceInput(amount=Decimal('25.10'), currency="USD", source=PriceHistorySource.MANUAL)
    test_schedule = ScheduleInput(period_unit=PeriodUnit.WEEK, period_interval=1, anchor_weekday=1)
    test_sub_manual = create_subscription_with_defaults(user=user_default, title=subscription_data_default['title'],
                                                        price=test_price_manual, schedule=test_schedule)
    now = timezone.now()
    with pytest.raises(ValueError):
        set_subscription_price(subscription=test_sub_manual, amount=Decimal('100.50'), currency="USD",
                               effective_from=effective_from(now), source=PriceHistorySource.MANUAL)