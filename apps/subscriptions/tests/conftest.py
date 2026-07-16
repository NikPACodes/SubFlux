import pytest
from decimal import Decimal
from typing import Optional
from types import SimpleNamespace
from django.utils import timezone
import datetime
from apps.subscriptions.models import Provider, VerifiedPrice, Category, Subscription, BillingSchedule


#--------- Базовые данные для моделей ---------
@pytest.fixture()
def subscription_data_default():
    """
    Базовые данные для тестовой подписки.
    """
    return {
        "title":"Тестовая подписка",
        "description":"Подписка на сервис",
        "status":"active",
        "started_at":"2001-01-01",
        "ended_at":"2001-02-01",
        "payment_method_label":"VISA",
        "owner_note":"заметки пользователя",
        "billing_timezone":"Asia/Yekaterinburg",
    }

@pytest.fixture()
def provider_data_default():
    """
    Базовые данные для тестового провайдера (сервиса).
    """
    return {
        "name":"Тест Провайдер",
        "slug":"test_provider",
        "description":"Тестовый провайдер",
        "is_active":"True",
    }

@pytest.fixture()
def category_data_default():
    """
    Базовые данные для тестовой категории.
    """
    return {
        "name":"Тестовая Категория",
        "slug":"test_category",
        "sort_order":"0",
    }

@pytest.fixture()
def verified_price_data_default():
    """
    Базовые данные для тестовой подтвержденной цены.
    """
    return {
        "plan_name":"Тестовый тариф",
        "region":"GLOBAL",
        "amount": 20.50,
        "currency":"USD",
        "period_unit":"month",
        "period_interval": 1,
        "platform":"web",
        "source":"admin",
        "valid_from":"2001-01-01",
        "valid_to":"2001-02-01",
        "is_active":"True",
    }


#--------- Базовые тестовые объекты ---------
@pytest.fixture()
def provider_default(db):
    """
    Базовый тестовый провайдер (сервис).
    """
    return Provider.objects.create(name="Тест Провайдер", slug="test_provider", description="Тестовый провайдер", is_active=True)

@pytest.fixture()
def category_default(db):
    """
    Базовая тестовая категория.
    """
    return Category.objects.create(name="Тестовая Категория", slug="test_category", sort_order=0)

@pytest.fixture()
def subscription_default(db, user_default):
    """
    Базовая подписка без связанных структур для Базового пользователя
    """
    return Subscription.objects.create(user=user_default, title="Тестовая подписка", description="Подписка на сервис",
                                       status="active", started_at="2001-01-01", ended_at="2001-02-01",
                                       payment_method_label="VISA", owner_note="заметки пользователя",
                                       billing_timezone="UTC")


#--------- Фабрики для создания тестовых объектов ---------
@pytest.fixture()
def provider_factory(db):
    """
    Фабрика создания провайдеров для тестов:
    ProviderX = provider_factory(name="...", slug="...", description="...")
    """
    def _create_provider(*, name: str, slug: str, description: str = " ") -> Provider:
        return Provider.objects.create(name=name, slug=slug, description=description, is_active=True)
    return _create_provider


@pytest.fixture()
def verified_price_factory(db):
    """
    Фабрика создания подтвержденных цен для тестов:
    VerifiedPriceX = verified_price_factory(provider=..., plan_name="...", amount=0.0, ...)
    """
    def _create_verified_price(*, provider: Provider, plan_name: str, amount: Decimal, currency: str = "USD",
                               region: str = "GLOBAL", period_unit: str = "month", period_interval: int = 1,
                               platform: str = "web", source: str = 'admin',
                               valid_from: timezone.datetime = timezone.now(), valid_to: Optional[timezone.datetime] = None,
                               is_active: bool = True) -> VerifiedPrice:
        return VerifiedPrice.objects.create(provider=provider, plan_name=plan_name,amount=amount, currency=currency,
                                            region=region, period_unit=period_unit, period_interval=period_interval,
                                            platform=platform, source=source, valid_from=valid_from, valid_to=valid_to,
                                            is_active=is_active)
    return _create_verified_price


@pytest.fixture()
def category_factory(db):
    """
    Фабрика создания категорий подписок для тестов:
    CategoryX = category_factory(name=..., slug="...", sort_order=0)
    """
    def _create_category(*, name: str, slug: str, sort_order: int = 0) -> Category:
        return Category.objects.create(name=name, slug=slug,sort_order=sort_order)
    return _create_category


@pytest.fixture()
def subscription_factory(db):
    """
    Фабрика создания подписок для тестов:
    SubscriptionX = subscription_factory(user=..., title="...", ...)
    """
    def _create_subscription(*, user,  title: str, description: str=None, status: str="active",
                             provider: Provider=None, category: Category=None,
                             started_at: datetime.date=None, ended_at: datetime.date=None,
                             payment_method_label: str=None, owner_note: str=None,
                             billing_timezone: str="UTC", meta=None) -> Subscription:
        return Subscription.objects.create(user=user, title=title, description=description, status=status,
                                           provider=provider, category=category, started_at=started_at, ended_at=ended_at,
                                           payment_method_label=payment_method_label, owner_note=owner_note,
                                           billing_timezone=billing_timezone, meta=meta)
    return _create_subscription


@pytest.fixture()
def schedule_factory(db):
    """
    Фабрика создания расписаний для тестов:
    BillingSchedule = schedule_factory(subscription=..., ...)
    """
    def _create_schedule(*, subscription, period_unit="month", period_interval=1, anchor_day=1,
                            anchor_weekday=None, trial_ends_at=None, grace_days=0, next_run_at=None, is_current=False):
        if next_run_at is None:
            next_run_at = timezone.now()
        return BillingSchedule.objects.create(subscription=subscription, period_unit=period_unit,
                                              period_interval=period_interval, anchor_day=anchor_day,
                                              anchor_weekday=anchor_weekday, trial_ends_at=trial_ends_at,
                                              grace_days=grace_days, next_run_at=next_run_at, is_current=is_current)
    return _create_schedule


#--------- Заглушки monkeypatch ---------
@pytest.fixture()
def monkeypatch_status_transition_calculation(monkeypatch):
    """
    Заглушка через фабрику (для передачи параметра) status_transition_calculation
    """
    def _monkeypatch_status_transition_calculation(result):
        monkeypatch.setattr("apps.subscriptions.services.subscription_service.status_transition_calculation",
                            lambda **kwargs: result)
        return result
    return _monkeypatch_status_transition_calculation


@pytest.fixture
def monkeypatch_create_schedule_from_remaining_period(monkeypatch):
    """
    Заглушка через фабрику (для передачи параметра) create_schedule_from_remaining_period
    """
    def _monkeypatch_create_schedule_from_remaining_period(next_run_at):
        state = {
            "called": False,
            "sub_id": None,
            "from_dt": None,
            "remaining_billing_seconds": None,
        }

        def fake_create_schedule_from_remaining_period(*, sub, remaining_billing_seconds, from_dt):
            state["called"] = True
            state["sub_id"] = sub.id
            state["from_dt"] = from_dt
            state["remaining_billing_seconds"] = remaining_billing_seconds
            return SimpleNamespace(next_run_at=next_run_at)

        monkeypatch.setattr("apps.subscriptions.services.subscription_service.create_schedule_from_remaining_period",
                            fake_create_schedule_from_remaining_period)
        return state
    return _monkeypatch_create_schedule_from_remaining_period


@pytest.fixture
def monkeypatch_create_schedule_from_existing(monkeypatch):
    """
    Заглушка через фабрику (для передачи параметра) create_schedule_from_existing
    """
    def _monkeypatch_create_schedule_from_existing(next_run_at):
        state = {
            "called": False,
            "sub_id": None,
            "from_dt": None,
        }

        def fake_create_schedule_from_existing(*, sub, from_dt):
            state["called"] = True
            state["sub_id"] = sub.id
            state["from_dt"] = from_dt
            return SimpleNamespace(next_run_at=next_run_at)

        monkeypatch.setattr("apps.subscriptions.services.subscription_service.create_schedule_from_existing",
                            fake_create_schedule_from_existing)
        return state
    return _monkeypatch_create_schedule_from_existing


@pytest.fixture
def monkeypatch_close_current_schedule(monkeypatch):
    """
    Заглушка через фабрику close_current_schedule
    """
    def _monkeypatch_close_current_schedule():
        state = {
            "called": False,
            "sub_id": None,
        }
        def fake_close_current_schedule(sub):
            state["called"] = True
            state["sub_id"] = sub.id
            return None

        monkeypatch.setattr("apps.subscriptions.services.subscription_service.close_current_schedule",
                            fake_close_current_schedule)

        return state
    return _monkeypatch_close_current_schedule