import pytest
from apps.subscriptions.models import PriceHistory
from django.db import IntegrityError

#---------- VerifiedPrice ----------
@pytest.mark.django_db
def test_create_verified_price(verified_price_data_default, verified_price_factory, provider_default):
    """
    Проверка создание доверенной цены (VerifiedPrice)
    """
    test_p = provider_default
    test_verified_price = verified_price_factory(provider=test_p,
                                                 plan_name=verified_price_data_default["plan_name"],
                                                 amount=verified_price_data_default["amount"])
    assert test_verified_price.id is not None
    assert test_verified_price.provider is not None


@pytest.mark.django_db
def test_uniq_verified_price(verified_price_factory, provider_default):
    """
    Проверка уникального ключа VerifiedPrice
    - 2 VerifiedPrice с одним ключом не могут быть активными (valid_to)
    """
    test_p = provider_default
    verified_price_factory(provider=test_p, plan_name="Тестовый тариф", platform="web", region="GLOBAL",
                           amount=100, currency="USD", period_unit="week", period_interval=2)
    with pytest.raises(IntegrityError):
        verified_price_factory(provider=test_p, plan_name="Тестовый тариф", platform="web", region="GLOBAL",
                                   amount=100, currency="USD", period_unit="week", period_interval=2)


@pytest.mark.django_db
def test_verified_price_amount_nonnegative(verified_price_data_default, verified_price_factory, provider_default):
    """
    amount не может быть меньше 0
    """
    test_p = provider_default
    with pytest.raises(IntegrityError):
        verified_price_factory(provider=test_p, plan_name=verified_price_data_default["plan_name"], amount=-10)

@pytest.mark.django_db
def test_verified_price_valid_to_gt_from(verified_price_data_default, verified_price_factory, provider_default):
    """
    valid_from не может быть позже valid_to
    """
    test_p = provider_default
    with pytest.raises(IntegrityError):
        verified_price_factory(provider=test_p, plan_name=verified_price_data_default["plan_name"], amount=100, currency="USD",
                               valid_from='2001-02-01', valid_to='2001-01-01',)


#---------- PriceHistory ----------
@pytest.mark.django_db
def test_price_history_manual(subscription_default):
    """
    Проверка создание записи истории цен (PriceHistory)
    Создание в Manual-режиме
    """
    test_sub = subscription_default
    test_ph_manual = PriceHistory.objects.create(subscription=test_sub, amount=10.25, currency="USD",
                                                 effective_from="2001-01-01", source="manual")

    assert test_ph_manual.id is not None
    assert test_ph_manual.source == "manual"
    assert test_ph_manual.verified_price is None
    assert all(ch is not None for ch in (test_ph_manual.amount, test_ph_manual.currency))


@pytest.mark.django_db
def test_price_history_verified(subscription_default, provider_default,
                                verified_price_data_default, verified_price_factory):
    """
    Проверка создание записи истории цен (PriceHistory)
    Создание в Verified-режиме
    """
    test_sub = subscription_default
    test_p = provider_default
    test_vp = verified_price_factory(provider=test_p, plan_name=verified_price_data_default["plan_name"],
                                     amount=verified_price_data_default["amount"])
    test_ph_verified = PriceHistory.objects.create(subscription=test_sub, verified_price=test_vp,
                                                 effective_from="2001-01-01", source="verified")

    assert test_ph_verified.id is not None
    assert test_ph_verified.source == "verified"
    assert test_ph_verified.verified_price is not None
    assert all(ch is None for ch in (test_ph_verified.amount, test_ph_verified.currency))


@pytest.mark.django_db
def test_price_history_amount_nonnegative(subscription_default):
    """
    amount не может быть меньше 0
    """
    test_sub = subscription_default
    with pytest.raises(IntegrityError):
        PriceHistory.objects.create(subscription=test_sub, amount=-10.5, currency="USD",
                                    effective_from="2001-01-01", source="manual")


@pytest.mark.django_db
def test_price_history_effective_to_gt_from(subscription_default):
    """
    effective_from не может быть позже effective_to
    """
    test_sub = subscription_default

    with pytest.raises(IntegrityError):
        PriceHistory.objects.create(subscription=test_sub, amount=10.25, currency="USD",
                                    effective_from='2001-02-01', effective_to='2001-01-01',
                                    source="manual")


@pytest.mark.django_db
def test_price_history_verified_or_manual(subscription_default, provider_default,
                                          verified_price_data_default, verified_price_factory):
    """
    Нельзя одновременно заполнять поля verified_price, amount, currency
    Для режима Verified поле verified_price -> обязательное, поля (amount, currency) -> пустые
    Для режима Manual поля (amount, currency) -> обязательные, поле verified_price -> пустое
    """
    test_sub = subscription_default
    test_p = provider_default
    test_vp = verified_price_factory(provider=test_p, plan_name=verified_price_data_default["plan_name"],
                                     amount=verified_price_data_default["amount"])

    with pytest.raises(IntegrityError):
        PriceHistory.objects.create(subscription=test_sub, verified_price=test_vp,
                                    amount=10.25, currency="USD",
                                    effective_from="2001-02-01", source="verified")


@pytest.mark.django_db
def test_price_history_uniq_subscription_active(subscription_default):
    """
    Возможна только одна активная цена для подписки (effective_to)
    """
    test_sub = subscription_default
    PriceHistory.objects.create(subscription=test_sub, amount=10.25, currency="USD",
                                 effective_from="2001-01-01", effective_to=None, source="manual")
    with pytest.raises(IntegrityError):
        PriceHistory.objects.create(subscription=test_sub, amount=25.00, currency="USD",
                                    effective_from="2001-02-01", effective_to=None, source="manual")