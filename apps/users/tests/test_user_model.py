import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError

User = get_user_model()


@pytest.mark.django_db
def test_username_required_at_db_level():
    """
    Username обязательно, поэтому запись с username = None должна упасть на уровне БД.
    """
    with pytest.raises(IntegrityError):
        User.objects.create_user(
            email="test_u2@test.com",
            username=None,
            password="TestPass12345!",
        )


@pytest.mark.django_db
def test_email_unique_constraint():
    """
    email уникален → второй раз создать с тем же email нельзя.
    """
    User.objects.create_user(email="same@test.com", username="test_u1", password="TestPass12345!")
    with pytest.raises(IntegrityError):
        User.objects.create_user(email="same@test.com", username="test_u2", password="TestPass12345!")


@pytest.mark.django_db
def test_username_unique_constraint():
    """
    username уникален → второй раз создать с тем же username нельзя.
    """
    User.objects.create_user(email="test_a@test.com", username="test_dup", password="TestPass12345!")
    with pytest.raises(IntegrityError):
        User.objects.create_user(email="test_b@test.com", username="test_dup", password="TestPass12345!")


@pytest.mark.django_db
def test_optional_fields_can_be_empty():
    """
    phone/bio/birth_date у нас необязательные — должны сохраняться как None.
    """
    test_u = User.objects.create_user(
        email="test_opt@test.com",
        username="test_opt",
        password="TestPass12345!",
        phone=None,
        bio=None,
        birth_date=None,
    )
    assert test_u.phone is None
    assert test_u.bio is None
    assert test_u.birth_date is None


@pytest.mark.django_db
def test_str_returns_username():
    """
    str у User возвращает username.
    """
    test_u = User.objects.create_user(email="test_str@example.com", username="test_strname", password="TestPass12345!")
    assert str(test_u) == "test_strname"