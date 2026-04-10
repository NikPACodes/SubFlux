import pytest
from apps.subscriptions.models import BillingSchedule
from django.db import IntegrityError
from django.utils import timezone

@pytest.mark.django_db
def test_billing_schedule_create(subscription_default):
    """
    Проверка создания правила списания (BillingSchedule)
    """
    test_sub = subscription_default
    test_billing_schedule = BillingSchedule.objects.create(subscription=test_sub, period_unit="week", period_interval=2,
                                                           anchor_weekday=1, next_run_at=timezone.now(), is_current=True)

    assert test_billing_schedule.id is not None
    assert test_billing_schedule.next_run_at is not None


@pytest.mark.django_db
def test_billing_schedule_interval(subscription_default):
    """
    Проверка создания правила с интервалом меньше 1 (period_interval)
    """
    test_sub = subscription_default
    with pytest.raises(IntegrityError):
        BillingSchedule.objects.create(subscription=test_sub, period_unit="week", period_interval=0,
                                       anchor_weekday=1, next_run_at=timezone.now(), is_current=True)


@pytest.mark.django_db
def test_uniq_active_billing_schedule(subscription_default):
    """
    Для 1 Subscription возможен только 1 актуальное BillingSchedule
    """
    test_sub = subscription_default
    BillingSchedule.objects.create(subscription=test_sub, period_unit="mouth", period_interval=1,
                                   anchor_day=1, next_run_at=timezone.now(), is_current=True)
    with pytest.raises(IntegrityError):
        BillingSchedule.objects.create(subscription=test_sub, period_unit="week", period_interval=2,
                                       anchor_weekday=1, next_run_at=timezone.now(), is_current=True)