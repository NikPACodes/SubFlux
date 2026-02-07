import pytest
from apps.subscriptions.models import Subscription, ProviderLink
from django.db import IntegrityError

@pytest.mark.django_db
def test_create_subscription(subscription_data_default,
                             user_data_default, create_user,
                             provider_data_default, provider_factory,
                             category_data_default, category_factory):
    """
    Проверка создания подписки
    - создание провайдера
    - создание категория
    - создание подписки
    """
    test_u = create_user(email=user_data_default["email"], username=user_data_default["username"], password=user_data_default["password"])
    test_p = provider_factory(name=provider_data_default["name"], slug=provider_data_default["slug"])
    test_cat = category_factory(name=category_data_default["name"], slug=category_data_default["slug"])
    test_sub = Subscription.objects.create(user=test_u,
                                           provider=test_p,
                                           category=test_cat,
                                           title=subscription_data_default["title"],
                                           description=subscription_data_default["description"],
                                           status=subscription_data_default["status"],
                                           started_at=subscription_data_default["started_at"],
                                           payment_method_label=subscription_data_default["payment_method_label"],
                                           owner_note=subscription_data_default["owner_note"],
                                           is_shared=subscription_data_default["is_shared"],
                                           billing_timezone=subscription_data_default["billing_timezone"])

    assert test_sub.id is not None
    assert test_sub.provider is not None
    assert test_sub.category is not None


@pytest.mark.django_db
def test_subscription_amount(subscription_data_default,
                             user_data_default, create_user):
    """
    current_price_amount не может быть меньше нуля
    """
    test_u = create_user(email=user_data_default["email"], username=user_data_default["username"],
                         password=user_data_default["password"])
    with pytest.raises(IntegrityError):
        Subscription.objects.create(user=test_u,
                                    title=subscription_data_default["title"],
                                    current_price_amount=-15.05)


@pytest.mark.django_db
def test_provider_link(provider_data_default, provider_factory):
    """
    Проверка создания ссылок сервисов (ProviderLink)
    """
    test_p = provider_factory(name=provider_data_default["name"], slug=provider_data_default["slug"])

    test_link = ProviderLink.objects.create(provider=test_p, region="GLOBAL",
                                            platform="web", link_type="account",
                                            url="https://example.com/", is_active=True)
    assert test_link.id is not None
    assert test_link.url is not None


@pytest.mark.django_db
def test_uniq_provider_link(provider_data_default, provider_factory):
    """
    У каждого провайдера только один URL регион+платформа+тип
    """
    test_p = provider_factory(name=provider_data_default["name"], slug=provider_data_default["slug"])

    ProviderLink.objects.create(provider=test_p, region="GLOBAL",
                                platform="web", link_type="account",
                                url="https://example.com/", is_active=True)

    with pytest.raises(IntegrityError):
        ProviderLink.objects.create(provider=test_p, region="GLOBAL",
                                    platform="web", link_type="account",
                                    url="https://example.com/", is_active=True)