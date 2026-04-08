import pytest
from decimal import Decimal
from typing import Optional
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
        "is_shared":"False",
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
                                       is_shared=False, billing_timezone="UTC")


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
                             is_shared: bool=False, billing_timezone: str="UTC", meta=None) -> Subscription:
        return Subscription.objects.create(user=user, title=title, description=description, status=status,
                                           provider=provider, category=category, started_at=started_at, ended_at=ended_at,
                                           payment_method_label=payment_method_label, owner_note=owner_note,
                                           is_shared=is_shared, billing_timezone=billing_timezone, meta=meta)
    return _create_subscription


@pytest.fixture
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