"""
Тесты на проверку корректной смены состояний (статусов) вынесены из test_subscription_service:
- Для предотвращения разрастания test_subscription_service
- Для явного выделения жизненного цикла в отдельный файл с проверками
- Для удобства тестирования
- Все тесты файла можно запустить по маркеру lifecycle_status
"""
import pytest
from datetime import timedelta
from django.utils import timezone
from apps.subscriptions.services.subscription_service import status_transition_calculation, set_subscription_status
from utils.enums import SubscriptionStatus

pytestmark = [pytest.mark.lifecycle_status]


def test_status_transition_calculation_to_trial(subscription_default):
    """
    Попытка расчёта нового состояния для TRIAL
    Статус TRIAL возможно установить только при создании
    """
    subscription_default.status = SubscriptionStatus.ACTIVE
    with pytest.raises(ValueError):
        status_transition_calculation(subscription=subscription_default,
                                      status_new=SubscriptionStatus.TRIAL,
                                      started_at=None,
                                      now=timezone.now())


def test_status_transition_calculation_to_delayed(subscription_default):
    """
    Расчёта нового состояния для статуса DELAYED (возможен только из EXPIRED)
    - Валидация отключена для упрощения
    - started_at > now
    - status и started_at успешно установлены
    - ended_at и next_billing_at отсутствуют
    - resume_schedule активирован
    - meta почищена
    - close_schedule и recalculate_schedule отключены
    """
    now = timezone.now()
    started_at = now + timedelta(days=10)

    subscription_default.status = SubscriptionStatus.EXPIRED
    subscription_default.started_at = None
    subscription_default.ended_at = now
    subscription_default.meta = {"paused_at": "old-value",
                                "remaining_billing_seconds": 1000}

    test_status_calc = status_transition_calculation(subscription=subscription_default,
                                                     status_new=SubscriptionStatus.DELAYED,
                                                     started_at=started_at,
                                                     now=now)

    assert test_status_calc["status"] == SubscriptionStatus.DELAYED
    assert test_status_calc["started_at"] == started_at
    assert test_status_calc["ended_at"] is None and test_status_calc["next_billing_at"] is None
    assert test_status_calc["resume_schedule"] is True
    assert test_status_calc["close_schedule"] is False and test_status_calc["recalculate_schedule"] is False
    assert test_status_calc["meta"]["paused_at"] is None
    assert test_status_calc["meta"]["remaining_billing_seconds"] is None


@pytest.mark.parametrize("old_status",
                         [SubscriptionStatus.DELAYED,
                          SubscriptionStatus.PAUSED,
                          SubscriptionStatus.CANCELED,
                          SubscriptionStatus.EXPIRED])
def test_status_transition_calculation_to_active(subscription_default, old_status):
    """
    Расчёта нового состояния для статуса ACTIVE:
    1) DELAYED -> ACTIVE
        - resume_schedule отключен
        - recalculate_schedule активирован
    2) PAUSED -> ACTIVE
        - resume_schedule активирован
        - recalculate_schedule отключен
    3) CANCELED -> ACTIVE
        - resume_schedule активирован
        - recalculate_schedule отключен
    4) EXPIRED -> ACTIVE
        - started_at = now
        - resume_schedule активирован
        - recalculate_schedule отключен
    - status успешно установлен
    - ended_at отсутствует
    - started_at <= now
    - close_schedule отключен
    - meta почищена
    """
    now = timezone.now()
    started_at = now - timedelta(days=10)

    subscription_default.status = old_status
    subscription_default.started_at = started_at
    subscription_default.meta = {"paused_at": "2026-01-01T00:00:00Z",
                                 "remaining_billing_seconds": 1000}

    test_status_calc = status_transition_calculation(subscription=subscription_default,
                                                     status_new=SubscriptionStatus.ACTIVE,
                                                     started_at=None,
                                                     now=now)

    assert test_status_calc["status"] == SubscriptionStatus.ACTIVE
    assert test_status_calc["started_at"] is not None
    assert test_status_calc["ended_at"] is None
    assert test_status_calc["close_schedule"] is False
    assert test_status_calc["meta"]["paused_at"] is None
    assert test_status_calc["meta"]["remaining_billing_seconds"] is None

    if old_status == SubscriptionStatus.EXPIRED:
        assert test_status_calc["started_at"] == now

    if old_status in (SubscriptionStatus.PAUSED, SubscriptionStatus.CANCELED, SubscriptionStatus.EXPIRED):
        assert test_status_calc["resume_schedule"] is True
    else:
        assert test_status_calc["resume_schedule"] is False

    if old_status == SubscriptionStatus.DELAYED:
        assert test_status_calc["recalculate_schedule"] is True
    else:
        assert test_status_calc["recalculate_schedule"] is False


def test_status_transition_calculation_to_paused(subscription_default):
    """
    Расчёта нового состояния для статуса PAUSED:
    - status успешно установлен
    - ended_at и next_billing_at отсутствуют
    - close_schedule активирован
    - resume_schedule и recalculate_schedule отключены
    - meta собрана
    """
    now = timezone.now()
    subscription_default.status = SubscriptionStatus.ACTIVE
    subscription_default.started_at = now - timedelta(days=10)
    subscription_default.next_billing_at = now + timedelta(days=5)
    subscription_default.meta = {"paused_at": None,
                                 "remaining_billing_seconds": None}

    test_status_calc = status_transition_calculation(subscription=subscription_default,
                                                     status_new=SubscriptionStatus.PAUSED,
                                                     started_at=None,
                                                     now=now)

    assert test_status_calc["status"] == SubscriptionStatus.PAUSED
    assert test_status_calc["ended_at"] is None and test_status_calc["next_billing_at"] is None
    assert test_status_calc["close_schedule"] is True
    assert test_status_calc["resume_schedule"] is False
    assert test_status_calc["recalculate_schedule"] is False
    assert test_status_calc["meta"]["paused_at"] is not None
    assert test_status_calc["meta"]["remaining_billing_seconds"] is not None


@pytest.mark.parametrize("next_billing_at",
                         [pytest.param(lambda now: now + timedelta(days=5), id="future"),
                          pytest.param(lambda now: now, id="now"),
                          pytest.param(lambda now: None, id="none")])
def test_status_transition_calculation_to_canceled(subscription_default, next_billing_at):
    """
    Расчёта нового состояния для статуса CANCELED:
    1) next_billing_at = now
        - установлен status EXPIRED
        - ended_at = now
    2) next_billing_at > now
        - установлен status CANCELED
        - ended_at = next_billing_at
    - next_billing_at отчищен
    - close_schedule активирован
    - resume_schedule и recalculate_schedule отключены
    - meta отчищен
    """
    now = timezone.now()
    subscription_default.status = SubscriptionStatus.ACTIVE
    subscription_default.started_at = now - timedelta(days=10)
    subscription_default.next_billing_at = next_billing_at(now)
    subscription_default.meta = {"paused_at": "2026-01-01T00:00:00Z",
                                 "remaining_billing_seconds": 1000}

    test_status_calc = status_transition_calculation(subscription=subscription_default,
                                                     status_new=SubscriptionStatus.CANCELED,
                                                     started_at=None,
                                                     now=now)

    if  next_billing_at(now) is None or next_billing_at(now) == now:
        assert test_status_calc["status"] == SubscriptionStatus.EXPIRED
        assert test_status_calc["ended_at"] == now
    else:
        assert test_status_calc["status"] == SubscriptionStatus.CANCELED
        assert test_status_calc["ended_at"] == next_billing_at(now)
    assert test_status_calc["next_billing_at"] is None
    assert test_status_calc["close_schedule"] is True
    assert test_status_calc["resume_schedule"] is False
    assert test_status_calc["recalculate_schedule"] is False
    assert test_status_calc["meta"]["paused_at"] is None
    assert test_status_calc["meta"]["remaining_billing_seconds"] is None


def test_status_transition_calculation_to_expired(subscription_default):
    """
    Расчёта нового состояния для статуса EXPIRED:
    - status успешно установлен
    - ended_at = now
    - next_billing_at отчищен
    - close_schedule активирован
    - resume_schedule и recalculate_schedule отключены
    - meta отчищен
    """
    now = timezone.now()
    subscription_default.status = SubscriptionStatus.ACTIVE
    subscription_default.started_at = now - timedelta(days=10)
    subscription_default.next_billing_at = now + timedelta(days=5)
    subscription_default.meta = {"paused_at": "2026-01-01T00:00:00Z",
                                 "remaining_billing_seconds": 1000}

    test_status_calc = status_transition_calculation(subscription=subscription_default,
                                                     status_new=SubscriptionStatus.EXPIRED,
                                                     started_at=None,
                                                     now=now)

    assert test_status_calc["status"] == SubscriptionStatus.EXPIRED
    assert test_status_calc["ended_at"] == now
    assert test_status_calc["next_billing_at"] is None
    assert test_status_calc["close_schedule"] is True
    assert test_status_calc["resume_schedule"] is False
    assert test_status_calc["recalculate_schedule"] is False
    assert test_status_calc["meta"]["paused_at"] is None
    assert test_status_calc["meta"]["remaining_billing_seconds"] is None


#--------------------------------------------------------------------------------
# set_subscription_status тестируется как оркестратор
#
# Следующие методы заменены на заглушки:
# - status_transition_calculation (тестируется отдельно)
# - close_current_schedule тестируется (тестируется отдельно)
# - create_schedule_from_remaining_period (тестируется отдельно)
# - create_schedule_from_existing (тестируется отдельно)
#--------------------------------------------------------------------------------
@pytest.mark.django_db
def test_set_subscription_status_resume_with_remaining_period(subscription_default,
                                                              monkeypatch_status_transition_calculation,
                                                              monkeypatch_create_schedule_from_remaining_period,
                                                              monkeypatch_create_schedule_from_existing):
    """
    Тест оркестратора по смене статуса для восстановления с остаточным периодом.
    Тестируем на примере PAUSED -> ACTIVE
    - данные подписки успешно обновлены
    - статус успешно установлен
    - метод create_schedule_from_remaining_period вызывался
    - остаточный период корректно передан в create_schedule_from_remaining_period
    """
    now = timezone.now()
    next_run_at = now + timedelta(days=5)

    sub = subscription_default
    sub.status = SubscriptionStatus.PAUSED
    sub.started_at = now - timedelta(days=10)
    sub.ended_at = None
    sub.next_billing_at = None
    sub.meta = {"paused_at": "2026-01-01T00:00:00Z",
                "remaining_billing_seconds": 1000}
    sub.save()

    status_calc = {
        "status": SubscriptionStatus.ACTIVE,
        "started_at": sub.started_at,
        "ended_at": None,
        "next_billing_at": None,
        "meta": {"paused_at": None,
                "remaining_billing_seconds": None},
        "close_schedule": False,
        "resume_schedule": True,
        "recalculate_schedule": False
    }

    # Заглушка status_transition_calculation (тестируется отдельно)
    monkeypatch_status_transition_calculation(status_calc)

    # Заглушка create_schedule_from_remaining_period (тестируется отдельно)
    called_remaining_period = monkeypatch_create_schedule_from_remaining_period(next_run_at)

    # Заглушка create_schedule_from_remaining_period (тестируется отдельно)
    called_existing = monkeypatch_create_schedule_from_existing(next_run_at)

    new_status_sub = set_subscription_status(subscription=sub,
                                             status_new=SubscriptionStatus.ACTIVE,
                                             now=now)

    assert sub.id == new_status_sub.id
    assert new_status_sub.status == SubscriptionStatus.ACTIVE
    assert new_status_sub.started_at == sub.started_at
    assert new_status_sub.ended_at is None
    assert new_status_sub.next_billing_at == next_run_at

    assert new_status_sub.meta["paused_at"] is None
    assert new_status_sub.meta["remaining_billing_seconds"] is None
    assert new_status_sub.next_billing_at == next_run_at

    assert called_remaining_period["called"] is True
    assert called_remaining_period["sub_id"] == sub.id
    assert called_remaining_period["remaining_billing_seconds"] == 1000
    assert called_remaining_period["from_dt"] == now
    assert called_existing["called"] is False


@pytest.mark.django_db
def test_set_subscription_status_resume_with_existing_schedule(subscription_default,
                                                               monkeypatch_status_transition_calculation,
                                                               monkeypatch_create_schedule_from_remaining_period,
                                                               monkeypatch_create_schedule_from_existing):
    """
    Тест оркестратора по смене статуса для восстановления с полным периодом.
    Тестируем на примере EXPIRED -> ACTIVE
    - данные подписки успешно обновлены
    - статус успешно установлен
    - метод create_schedule_from_existing вызывался
    """


    now = timezone.now()
    next_run_at = now + timedelta(days=5)

    sub = subscription_default
    sub.status = SubscriptionStatus.EXPIRED
    sub.started_at = now - timedelta(days=10)
    sub.ended_at = now
    sub.next_billing_at = None
    sub.meta = {"paused_at": None,
                "remaining_billing_seconds": None}
    sub.save()

    status_calc = {
        "status": SubscriptionStatus.ACTIVE,
        "started_at": now,
        "ended_at": None,
        "next_billing_at": None,
        "meta": {"paused_at": None,
                 "remaining_billing_seconds": None},
        "close_schedule": False,
        "resume_schedule": True,
        "recalculate_schedule": False
    }

    # Заглушка status_transition_calculation (тестируется отдельно)
    monkeypatch_status_transition_calculation(status_calc)

    # Заглушка create_schedule_from_remaining_period (тестируется отдельно)
    called_remaining_period = monkeypatch_create_schedule_from_remaining_period(next_run_at)

    # Заглушка create_schedule_from_remaining_period (тестируется отдельно)
    called_existing = monkeypatch_create_schedule_from_existing(next_run_at)

    new_status_sub = set_subscription_status(subscription=sub,
                                             status_new=SubscriptionStatus.ACTIVE,
                                             now=now)
    assert new_status_sub.id == sub.id
    assert new_status_sub.status == SubscriptionStatus.ACTIVE
    assert new_status_sub.started_at == now
    assert new_status_sub.ended_at is None
    assert new_status_sub.next_billing_at == next_run_at
    assert new_status_sub.meta["paused_at"] is None
    assert new_status_sub.meta["remaining_billing_seconds"] is None

    assert called_existing["called"] is True
    assert called_existing["sub_id"] == sub.id
    assert called_existing["from_dt"] == now
    assert called_remaining_period["called"] is False


@pytest.mark.django_db
def test_set_subscription_status_close_current_schedule(subscription_default,
                                                        monkeypatch_status_transition_calculation,
                                                        monkeypatch_close_current_schedule):
    """
    Тест оркестратора по смене статуса для закрытия действующего расписания.
    Тестируем на примере ACTIVE -> EXPIRED
    - данные подписки успешно обновлены
    - статус успешно установлен
    - метод close_current_schedule вызывался
    """
    now = timezone.now()
    next_run_at = now + timedelta(days=5)

    sub = subscription_default
    sub.status = SubscriptionStatus.ACTIVE
    sub.started_at = now - timedelta(days=10)
    sub.ended_at = None
    sub.next_billing_at = next_run_at
    sub.meta = {"paused_at": None,
                "remaining_billing_seconds": None}
    sub.save()

    status_calc = {
        "status": SubscriptionStatus.EXPIRED,
        "started_at": sub.started_at,
        "ended_at": now,
        "next_billing_at": None,
        "meta": {"paused_at": None,
                 "remaining_billing_seconds": None},
        "close_schedule": True,
        "resume_schedule": False,
        "recalculate_schedule": False
    }

    # Заглушка status_transition_calculation (тестируется отдельно)
    monkeypatch_status_transition_calculation(status_calc)

    called_close_sched = monkeypatch_close_current_schedule()

    new_status_sub = set_subscription_status(subscription=sub,
                                             status_new=SubscriptionStatus.ACTIVE,
                                             now=now)
    assert new_status_sub.id == sub.id
    assert new_status_sub.status == SubscriptionStatus.EXPIRED
    assert new_status_sub.started_at == sub.started_at
    assert new_status_sub.ended_at == now
    assert new_status_sub.next_billing_at is None
    assert new_status_sub.meta["paused_at"] is None
    assert new_status_sub.meta["remaining_billing_seconds"] is None

    assert called_close_sched["called"] is True
    assert called_close_sched["sub_id"] == sub.id


@pytest.mark.django_db
def test_set_subscription_status_nothing_changed(subscription_default,
                                                 monkeypatch_status_transition_calculation,
                                                 mocker):
    """
    Тест оркестратора по смене статуса при отсутствии изменений
    - данные подписки не изменяются
    - сохранения не происходят
    """
    now = timezone.now()

    sub = subscription_default
    sub.status = SubscriptionStatus.ACTIVE
    sub.started_at = now - timedelta(days=10)
    sub.ended_at = None
    sub.next_billing_at = now + timedelta(days=5)
    sub.meta = {"paused_at": None,
                "remaining_billing_seconds": None}
    sub.save()

    status_calc = {
        "status": sub.status,
        "started_at": sub.started_at,
        "ended_at": sub.ended_at,
        "next_billing_at": sub.next_billing_at,
        "meta": sub.meta,
        "close_schedule": False,
        "resume_schedule": False,
        "recalculate_schedule": False,
    }

    # Заглушка status_transition_calculation (тестируется отдельно)
    monkeypatch_status_transition_calculation(status_calc)

    mock_save = mocker.patch("apps.subscriptions.models.Subscription.save")

    new_status_sub = set_subscription_status(subscription=sub,
                                             status_new=SubscriptionStatus.ACTIVE,
                                             now=now)

    mock_save.assert_not_called()
    assert sub.id == new_status_sub.id
    assert sub.update_at == new_status_sub.update_at