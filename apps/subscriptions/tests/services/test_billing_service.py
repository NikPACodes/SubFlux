import pytest
from datetime import datetime, timedelta
from django.core.exceptions import ValidationError
from django.utils import timezone
from zoneinfo import ZoneInfo
from apps.subscriptions.services.billing_service import (get_current_schedule,
                                                         get_last_schedule,
                                                         close_current_schedule,
                                                         create_schedule_from_existing,
                                                         create_schedule_from_remaining_period,
                                                         recalculate_schedule_next_run,
                                                         sync_subscription_next_billing)
from utils.enums import PeriodUnit


#--------------------------- Тесты получения расписания ---------------------------
@pytest.mark.django_db
def test_get_current_schedule(subscription_default, schedule_factory):
    """
    Попытка получения активного расписания
    - получаем расписание is_current=True
    """
    test_sched_current = schedule_factory(subscription=subscription_default, is_current=True)
    schedule_factory(subscription=subscription_default, is_current=False)
    test_sched = get_current_schedule(subscription_default)

    assert test_sched.id is not None
    assert test_sched.id == test_sched_current.id
    assert test_sched.is_current == True


@pytest.mark.django_db
def test_get_current_schedule_none(subscription_default):
    """
    Получение активного расписания возвращает None при его отсутствии
    """
    test_sched = get_current_schedule(subscription_default)
    assert test_sched is None


@pytest.mark.django_db
def test_get_last_schedule(subscription_default, schedule_factory):
    """
    Попытка получение последнего расписания (на основе даты создания)
    - Получаем последнюю запись BillingSchedule по Subscription
    - Игнорируем is_current = True, если оно не последнее
    """
    schedule_factory(subscription=subscription_default, is_current=True)
    last_sched = schedule_factory(subscription=subscription_default, is_current=False)
    test_sched_last = get_last_schedule(subscription_default)

    assert test_sched_last.id is not None
    assert test_sched_last.id == last_sched.id
    assert test_sched_last.is_current == False


@pytest.mark.django_db
def test_get_last_schedule_none(subscription_default):
    """
    Получение последнего расписания возвращает None при его отсутствии
    """
    test_sched_last = get_last_schedule(subscription_default)
    assert test_sched_last is None


#--------------------------- Тесты закрытия расписания ---------------------------
@pytest.mark.django_db
def test_close_current_schedule(subscription_default, schedule_factory):
    current = schedule_factory(subscription=subscription_default, is_current=True)
    test_close_sched = close_current_schedule(subscription_default)
    current.refresh_from_db()

    assert test_close_sched is not None
    assert test_close_sched.id == current.id
    assert current.is_current is False


@pytest.mark.django_db
def test_close_current_schedule_none(subscription_default):
    """
    Попытка завершить активное расписание возвращает None при его отсутствии
    """
    test_close_sched = close_current_schedule(subscription_default)
    assert test_close_sched is None


#--------------------------- Тесты создания расписаний ---------------------------
@pytest.mark.django_db
def test_create_schedule_from_existing(subscription_default, schedule_factory):
    """
    Создание активного расписания на основе базового, на полный период:
    - Расписание корректно создано по шаблону
    - Пересчет next_run_at выполнен корректно
    """
    utc_tz = ZoneInfo('UTC')
    from_dt = datetime(2026, 1, 5, 0, 0, tzinfo=utc_tz)  # ПН 05.01.2026 UTC
    recalc_next_run_at = datetime(2026, 1, 12, 0, 0, tzinfo=utc_tz)  # ПН 12.01.2026 UTC
    last_sched = schedule_factory(subscription=subscription_default,
                                  period_unit=PeriodUnit.WEEK,
                                  period_interval=1,
                                  anchor_day=None,
                                  anchor_weekday=0, # ПН
                                  trial_ends_at=None,
                                  grace_days=3,
                                  next_run_at=from_dt,
                                  is_current=False)
    test_new_sched = create_schedule_from_existing(subscription_default, from_dt=from_dt)

    assert test_new_sched.id != last_sched.id
    assert test_new_sched.subscription_id == subscription_default.id
    assert test_new_sched.period_unit == last_sched.period_unit
    assert test_new_sched.period_interval == last_sched.period_interval
    assert test_new_sched.anchor_day == last_sched.anchor_day
    assert test_new_sched.anchor_weekday == last_sched.anchor_weekday
    assert test_new_sched.trial_ends_at == last_sched.trial_ends_at
    assert test_new_sched.grace_days == last_sched.grace_days
    assert test_new_sched.is_current is True
    assert test_new_sched.next_run_at == recalc_next_run_at


@pytest.mark.django_db
def test_create_schedule_from_existing_raises_last_schedule(subscription_default):
    """
    Невозможно создать расписание при отсутствии предыдущего (базового)
    """
    with pytest.raises(ValidationError):
        create_schedule_from_existing(subscription_default)


@pytest.mark.django_db
def test_create_schedule_from_remaining_period(subscription_default, schedule_factory):
    """
    Создание активного расписания на основе базового, на остаточный период:
    - Расписание корректно создано по шаблону
    - Пересчет next_run_at выполнен корректно
    - Пересчет anchor_weekday для WEEK корректен
    """
    utc_tz = ZoneInfo('UTC')
    from_dt = datetime(2026, 1, 5, 0, 0, tzinfo=utc_tz)  # ПН 05.01.2026 UTC
    recalc_next_run_at = datetime(2026, 1, 7, 0, 0, tzinfo=utc_tz)  # СР 07.01.2026 UTC
    recalc_anchor_weekday = 2 # СР
    last_sched = schedule_factory(subscription=subscription_default,
                                  period_unit=PeriodUnit.WEEK,
                                  period_interval=1,
                                  anchor_day=None,
                                  anchor_weekday=0, # ПН
                                  trial_ends_at=None,
                                  grace_days=3,
                                  next_run_at=from_dt,
                                  is_current=False)
    test_new_sched = create_schedule_from_remaining_period(sub=subscription_default,
                                                           remaining_billing_seconds=172800, # 2 дня в сек
                                                           from_dt=from_dt)
    assert test_new_sched.id != last_sched.id
    assert test_new_sched.subscription_id == subscription_default.id
    assert test_new_sched.period_unit == last_sched.period_unit
    assert test_new_sched.period_interval == last_sched.period_interval
    assert test_new_sched.anchor_day == last_sched.anchor_day
    assert test_new_sched.anchor_weekday == recalc_anchor_weekday
    assert test_new_sched.trial_ends_at == last_sched.trial_ends_at
    assert test_new_sched.grace_days == last_sched.grace_days
    assert test_new_sched.is_current is True
    assert test_new_sched.next_run_at == recalc_next_run_at


@pytest.mark.django_db
@pytest.mark.parametrize("remaining_billing_seconds",
                         [pytest.param(None, id="Отсутствует"),
                          pytest.param(-100, id="Отрицательный"),
                          pytest.param(172800, id="Корректный")])
def test_create_schedule_from_remaining_period_raises(subscription_default, remaining_billing_seconds):
    """
    Проверка исключений при создании расписания на неполный период на основе предыдущего:
    - remaining_billing_seconds является обязательным
    - remaining_billing_seconds не отрицательный
    - должно существовать предыдущее (базовое) расписание

    !!! Проверка last_schedule идет после всех проверок, если она будет перемещена необходимо откорректировать тест
    """
    with pytest.raises(ValidationError):
        create_schedule_from_remaining_period(sub=subscription_default,
                                              remaining_billing_seconds=remaining_billing_seconds)


#--------------------------- Тесты пересчета расписаний ---------------------------
@pytest.mark.django_db
def test_recalculate_schedule_next_run_for_remaining_period(subscription_default, schedule_factory):
    """
    Проверка пересчета на неполный период (на примере MONTH):
    - Пересчет anchor_day для MONTH корректен
    - Пересчет next_run_at выполнен корректно

    !!! Пересчет anchor_weekday для WEEK включен в test_create_schedule_from_remaining_period
    """
    utc_tz = ZoneInfo('UTC')
    from_dt = datetime(2026, 1, 25, 0, 0, tzinfo=utc_tz)  # 25.01.2026
    recalc_next_run_at = datetime(2026, 2, 4, 0, 0, tzinfo=utc_tz)  # 04.02.2026

    sched = schedule_factory(subscription=subscription_default,
                             period_unit=PeriodUnit.MONTH,
                             period_interval = 1,
                             anchor_day = 1,
                             next_run_at=from_dt,
                             is_current=True)
    test_recalc_sched = recalculate_schedule_next_run(sched,
                                                      from_dt=from_dt,
                                                      remaining_billing_seconds=864000)  # 10 дней
    sched.refresh_from_db()

    assert test_recalc_sched.id == sched.id
    assert sched.anchor_day == recalc_next_run_at.day
    assert sched.next_run_at == recalc_next_run_at


@pytest.mark.django_db
def test_recalculate_schedule_next_run_for_remaining_period_raises(subscription_default, schedule_factory):
    """
    Попытка пересчета с отрицательным remaining_billing_seconds
    """
    sched = schedule_factory(subscription=subscription_default, is_current=True)
    with pytest.raises(ValidationError):
        recalculate_schedule_next_run(sched, from_dt=timezone.now(), remaining_billing_seconds=-100)


@pytest.mark.django_db
def test_recalculate_schedule_next_run_for_full_period(subscription_default, schedule_factory):
    """
    Проверка пересчета на полный период (на примере MONTH):
    - Пересчет next_run_at выполнен корректно
    - Последний день месяц корректно пересчитан 31.01 -> 28.02 (т.к. 31.02 нет)

    !!! anchor_day не пересчитывается т.к. переход 31.01 -> 28.02 является частным случаем
        и не должен менять расписание, а только корректно найти последний день месяца
    """
    utc_tz = ZoneInfo('UTC')
    from_dt = datetime(2026, 1, 31, 0, 0, tzinfo=utc_tz)  # 31.01.2026
    recalc_next_run_at = datetime(2026, 2, 28, 0, 0, tzinfo=utc_tz)  # 28.02.2026

    sched = schedule_factory(subscription=subscription_default,
                             period_unit=PeriodUnit.MONTH,
                             period_interval = 1,
                             anchor_day = 31,
                             next_run_at=from_dt,
                             is_current=True)
    test_recalc_sched = recalculate_schedule_next_run(sched, from_dt=from_dt)
    sched.refresh_from_db()

    assert test_recalc_sched.id == sched.id
    assert sched.next_run_at == recalc_next_run_at
    assert sched.anchor_day == 31


@pytest.mark.django_db
def test_recalculate_schedule_next_run_for_trial(subscription_default, schedule_factory):
    """
    Проверка пересчета на полный период (на примере DAY) с учетом TRIAL периода:
    - Пересчет next_run_at выполнен с учетом завершения TRIAL (trial_ends_at)
    next_run_at = trial_ends_at + полный период

    !!! anchor_day не пересчитывается т.к. переход 31.01 -> 28.02 является частным случаем
        и не должен менять расписание, а только корректно найти последний день месяца
    """
    utc_tz = ZoneInfo('UTC')
    from_dt = datetime(2026, 1, 1, 0, 0, tzinfo=utc_tz)              # 01.01.2026
    trial_ends_at = from_dt + timedelta(days=5)                                                     # 06.01.2026
    recalc_next_run_at = datetime(2026, 1, 16, 0, 0, tzinfo=utc_tz)  # 16.01.2026

    sched = schedule_factory(subscription=subscription_default,
                             period_unit=PeriodUnit.DAY,
                             period_interval=10,
                             trial_ends_at=trial_ends_at,
                             is_current=True)
    test_recalc_sched = recalculate_schedule_next_run(sched, from_dt=from_dt)
    sched.refresh_from_db()

    assert test_recalc_sched.id == sched.id
    assert sched.next_run_at == recalc_next_run_at


@pytest.mark.django_db
def test_recalculate_schedule_next_run_raises_unknown_period_unit(subscription_default, schedule_factory):
    """
    Попытка пересчета с неверным периодом (period_unit)
    """
    schedule = schedule_factory(subscription=subscription_default,
                                period_unit="unknown",
                                is_current=True)
    with pytest.raises(ValidationError):
        recalculate_schedule_next_run(schedule, from_dt=timezone.now())


#--------------------------- Тесты синхронизации денормализованных полей  ---------------------------
@pytest.mark.django_db
@pytest.mark.parametrize("is_current",
                         [pytest.param(True, id="Есть расписание"),
                          pytest.param(True, id="Нет расписание")])
def test_sync_subscription_next_billing(subscription_default, schedule_factory, is_current):
    """
    Проверка синхронизации денормализованной Subscription.next_billing_at
    - При наличии активного расписания (is_current=True), обновляется next_billing_at
    - При отсутствии активного расписания (is_current=False), next_billing_at затирается
    """
    utc_tz = ZoneInfo('UTC')
    subscription_default.next_billing_at = datetime(2026, 1, 1, 0, 0, tzinfo=utc_tz)
    subscription_default.save(update_fields=["next_billing_at"])

    test_sched = schedule_factory(subscription=subscription_default,
                                  next_run_at=timezone.now(),
                                  is_current=is_current)

    sync_subscription_next_billing(subscription_default)
    subscription_default.refresh_from_db()

    if is_current:
        assert subscription_default.next_billing_at == test_sched.next_run_at
    else:
        assert subscription_default.next_billing_at is None