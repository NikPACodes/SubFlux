import pytest
from apps.subscriptions.models import BillingSchedule
from django.db import IntegrityError
from django.utils import timezone

@pytest.mark.django_db
def test_billing_schedule_create(user_data_default, create_user,
                                 subscription_data_default, subscription_factory):
    """
    Проверка создания правила списания (BillingSchedule)
    """
    test_u = create_user(email=user_data_default["email"], username=user_data_default["username"],
                         password=user_data_default["password"])
    test_sub = subscription_factory(user=test_u, title=subscription_data_default["title"])

    test_billing_schedule = BillingSchedule.objects.create(subscription=test_sub, period_unit="week", period_interval=2,
                                                           anchor_weekday=1, next_run_at=timezone.now(), is_current=True)

    assert test_billing_schedule.id is not None
    assert test_billing_schedule.next_run_at is not None


@pytest.mark.django_db
def test_billing_schedule_interval(user_data_default, create_user,
                                   subscription_data_default, subscription_factory):
    """
    Проверка создания правила с интервалом меньше 1 (period_interval)
    """
    test_u = create_user(email=user_data_default["email"], username=user_data_default["username"],
                         password=user_data_default["password"])
    test_sub = subscription_factory(user=test_u, title=subscription_data_default["title"])

    with pytest.raises(IntegrityError):
        BillingSchedule.objects.create(subscription=test_sub, period_unit="week", period_interval=0,
                                       anchor_weekday=1, next_run_at=timezone.now(), is_current=True)


@pytest.mark.django_db
def test_uniq_active_billing_schedule(user_data_default, create_user,
                                   subscription_data_default, subscription_factory):
    """
    Для 1 Subscription возможен только 1 актуальное BillingSchedule
    """
    test_u = create_user(email=user_data_default["email"], username=user_data_default["username"],
                         password=user_data_default["password"])
    test_sub = subscription_factory(user=test_u, title=subscription_data_default["title"])

    BillingSchedule.objects.create(subscription=test_sub, period_unit="mouth", period_interval=1,
                                   anchor_day=1, next_run_at=timezone.now(), is_current=True)
    with pytest.raises(IntegrityError):
        BillingSchedule.objects.create(subscription=test_sub, period_unit="week", period_interval=2,
                                       anchor_weekday=1, next_run_at=timezone.now(), is_current=True)