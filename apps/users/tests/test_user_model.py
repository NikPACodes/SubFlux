import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError

User = get_user_model()


@pytest.mark.django_db
def test_username_required_at_db_level(user_pass):
    """
    Username обязательно, поэтому запись с username = None должна упасть на уровне БД.
    """
    with pytest.raises(IntegrityError):
        User.objects.create_user(
            email="test_u2@test.com",
            username=None,
            password=user_pass,
        )


@pytest.mark.django_db
def test_email_unique_constraint(user_pass):
    """
    email уникален → второй раз создать с тем же email нельзя.
    """
    User.objects.create_user(email="same@test.com", username="test_u1", password=user_pass)
    with pytest.raises(IntegrityError):
        User.objects.create_user(email="same@test.com", username="test_u2", password=user_pass)


@pytest.mark.django_db
def test_username_unique_constraint(user_pass):
    """
    username уникален → второй раз создать с тем же username нельзя.
    """
    User.objects.create_user(email="test_a@test.com", username="test_dup", password=user_pass)
    with pytest.raises(IntegrityError):
        User.objects.create_user(email="test_b@test.com", username="test_dup", password=user_pass)


@pytest.mark.django_db
def test_optional_fields_can_be_empty(user_pass):
    """
    phone/bio/birth_date у нас необязательные — должны сохраняться как None.
    """
    test_u = User.objects.create_user(
        email="test_opt@test.com",
        username="test_opt",
        password=user_pass,
        phone=None,
        bio=None,
        birth_date=None,
    )
    assert test_u.phone is None
    assert test_u.bio is None
    assert test_u.birth_date is None


@pytest.mark.django_db
def test_str_returns_username(user_pass):
    """
    str у User возвращает username.
    """
    test_u = User.objects.create_user(email="test_str@example.com", username="test_strname", password=user_pass)
    assert str(test_u) == "test_strname"