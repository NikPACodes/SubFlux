import pytest
from decimal import Decimal

from django.utils import timezone
from django.core.validators import ValidationError

from apps.subscriptions.services.subscription_service import (PriceInput, ScheduleInput,
                                                              create_subscription_with_defaults,
                                                              set_subscription_price)

from utils.date_calculator import get_tzinfo, next_week


# ---------- create_subscription_with_defaults ----------
@pytest.mark.django_db
def test_service_create_subscription_manual_full(subscription_data_default,
                                                 user_data_default, create_user,
                                                 provider_data_default, provider_factory,
                                                 category_data_default, category_factory):
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
    test_u = create_user(email=user_data_default['email'], username=user_data_default['username'],
                         password=user_data_default['password'])
    test_p = provider_factory(name=provider_data_default["name"], slug=provider_data_default["slug"])
    test_cat = category_factory(name=category_data_default["name"], slug=category_data_default["slug"])

    test_price_manual = PriceInput(amount=Decimal('20.10'),
                                   currency="USD",
                                   source="manual")

    test_schedule = ScheduleInput(period_unit="week",
                                  period_interval=1,
                                  anchor_weekday=1,
                                  billing_timezone="Europe/Moscow")

    test_service_subscription_manual = create_subscription_with_defaults(user=test_u,
                                                                         title=subscription_data_default['title'],
                                                                         provider=test_p,
                                                                         category=test_cat,
                                                                         status="active",
                                                                         started_at=timezone.now(),
                                                                         ended_at=None,
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


    test_billing_schedules = test_service_subscription_manual.billing_schedules.first()

    tzone = get_tzinfo(test_service_subscription_manual.billing_timezone)  # Получение тайм зоны подписки
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
    assert test_billing_schedules.next_run_at == test_service_subscription_manual.next_billing_at


@pytest.mark.django_db
def test_service_create_subscription_verified_full(subscription_data_default,
                                                   user_data_default, create_user,
                                                   provider_data_default, provider_factory,
                                                   category_data_default, category_factory,
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
    test_u = create_user(email=user_data_default['email'], username=user_data_default['username'],
                         password=user_data_default['password'])
    test_p = provider_factory(name=provider_data_default["name"], slug=provider_data_default["slug"])
    test_cat = category_factory(name=category_data_default["name"], slug=category_data_default["slug"])

    test_vp = verified_price_factory(provider=test_p, plan_name=verified_price_data_default["plan_name"],
                                     amount=verified_price_data_default["amount"])

    test_price_verified = PriceInput(verified_price=test_vp,
                                     source="verified")

    test_schedule = ScheduleInput(period_unit="week",
                                  period_interval=1,
                                  anchor_weekday=1,
                                  billing_timezone="Europe/Moscow")

    test_service_subscription_verified = create_subscription_with_defaults(user=test_u,
                                                                           title="Тестовая подписка 1",
                                                                           provider=test_p,
                                                                           category=test_cat,
                                                                           status="active",
                                                                           started_at=timezone.now(),
                                                                           ended_at=None,
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


@pytest.mark.django_db
def test_service_create_subscription_verified_or_manual(subscription_data_default,
                                                        user_data_default, create_user,
                                                        provider_data_default, provider_factory,
                                                        verified_price_data_default, verified_price_factory):
    """
    Нельзя заполнять одновременно поля verified_price, amount, currency в PriceInput
    - Для Verified -> Заполнено verified_price. Пустые amount и currency.
    - Для Manual -> Заполнены amount и currency. Пустое verified_price.
    """
    test_u = create_user(email=user_data_default['email'], username=user_data_default['username'],
                         password=user_data_default['password'])
    test_p = provider_factory(name=provider_data_default["name"], slug=provider_data_default["slug"])

    test_vp = verified_price_factory(provider=test_p, plan_name=verified_price_data_default["plan_name"],
                                     amount=verified_price_data_default["amount"])

    test_price_verified = PriceInput(verified_price=test_vp,
                                     amount=Decimal('20.10'),
                                     currency="USD",
                                     source="verified")

    test_schedule = ScheduleInput(period_unit="week", period_interval=1, anchor_weekday=1)

    with pytest.raises(ValidationError):
        create_subscription_with_defaults(user=test_u, title="Тестовая подписка 1", provider=test_p,
                                          status="active", price=test_price_verified, schedule=test_schedule)


@pytest.mark.django_db
def test_service_create_subscription_anchor(subscription_data_default, user_data_default, create_user):
    """
    Для ScheduleInput обязательно заполнение anchor_* для недели и месяца
    - Week -> anchor_weekday
    - Month -> anchor_day
    """
    test_u = create_user(email=user_data_default['email'], username=user_data_default['username'],
                         password=user_data_default['password'])

    test_price = PriceInput(amount=Decimal('20.10'), currency="USD", source="manual")

    test_schedule = ScheduleInput(period_unit="week")

    with pytest.raises(ValidationError):
        create_subscription_with_defaults(user=test_u, title="Тестовая подписка 1", status="active",
                                          price=test_price, schedule=test_schedule)


# ---------- set_subscription_price ----------