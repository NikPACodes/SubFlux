import pytest
from apps.subscriptions.models import Subscription, ProviderLink
from django.db import IntegrityError

@pytest.mark.django_db
def test_create_subscription(subscription_data_default,
                             user_default, provider_default, category_default):
    """
    Проверка создания подписки
    - создание провайдера
    - создание категория
    - создание подписки
    """
    test_u = user_default
    test_p = provider_default
    test_cat = category_default
    test_sub = Subscription.objects.create(user=test_u,
                                           provider=test_p,
                                           category=test_cat,
                                           title=subscription_data_default["title"],
                                           description=subscription_data_default["description"],
                                           status=subscription_data_default["status"],
                                           started_at=subscription_data_default["started_at"],
                                           payment_method_label=subscription_data_default["payment_method_label"],
                                           owner_note=subscription_data_default["owner_note"],
                                           billing_timezone=subscription_data_default["billing_timezone"])

    assert test_sub.id is not None
    assert test_sub.provider is not None
    assert test_sub.category is not None


@pytest.mark.django_db
def test_subscription_raises_amount(subscription_data_default, user_default):
    """
    current_price_amount не может быть меньше нуля
    """
    test_u = user_default
    with pytest.raises(IntegrityError):
        Subscription.objects.create(user=test_u,
                                    title=subscription_data_default["title"],
                                    current_price_amount=-15.05)


@pytest.mark.django_db
def test_provider_link(provider_default):
    """
    Проверка создания ссылок сервисов (ProviderLink)
    """
    test_p = provider_default
    test_link = ProviderLink.objects.create(provider=test_p, region="GLOBAL",
                                            platform="web", link_type="account",
                                            url="https://example.com/", is_active=True)
    assert test_link.id is not None
    assert test_link.url is not None


@pytest.mark.django_db
def test_uniq_provider_raises_link(provider_default):
    """
    У каждого провайдера только один URL регион+платформа+тип
    """
    test_p = provider_default
    ProviderLink.objects.create(provider=test_p, region="GLOBAL",
                                platform="web", link_type="account",
                                url="https://example.com/", is_active=True)

    with pytest.raises(IntegrityError):
        ProviderLink.objects.create(provider=test_p, region="GLOBAL",
                                    platform="web", link_type="account",
                                    url="https://example.com/", is_active=True)