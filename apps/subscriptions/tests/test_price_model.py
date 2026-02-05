import pytest

@pytest.mark.django_db
def test_create_verified_price(verified_price_data_default, verified_price_factory,
                               provider_data_default, provider_factory):
    """
    Проверка создание доверенной цены (VerifiedPrice)
    """

    test_p = provider_factory(name=provider_data_default["name"], slug=provider_data_default["slug"])
    test_verified_price = verified_price_factory(provider=test_p,
                                                 plan_name=verified_price_data_default["plan_name"],
                                                 amount=verified_price_data_default["amount"])
    assert test_verified_price.id is not None
    assert test_verified_price.provider is not None