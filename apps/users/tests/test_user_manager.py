import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
def test_create_user_success(user_data_default):
    """
    Проверяем корректность создание пользователяЖ
    - сохранение полей
    - хеширование пароля
    - флаги staff/superuser = False
    """
    test_u = User.objects.create_user(
        email=user_data_default["email"],
        username=user_data_default["username"],
        password=user_data_default["password"],
    )

    assert test_u.id is not None
    assert test_u.email == user_data_default["email"]
    assert test_u.username == user_data_default["username"]

    #Проверка хеширования пароля
    assert test_u.password != user_data_default["password"]
    assert test_u.check_password(user_data_default["password"]) is True

    assert test_u.is_staff is False
    assert test_u.is_superuser is False
    assert test_u.is_active is True


@pytest.mark.django_db
def test_create_user_without_email_raises(user_data_default):
    """
    Email обязателен.
    Если email пустой — ValueError.
    """
    with pytest.raises(ValueError):
        User.objects.create_user(
            email="",
            username=user_data_default["username"],
            password=user_data_default["password"],
        )


@pytest.mark.django_db
def test_create_user_without_password_sets_unusable(user_data_default):
    """
    Если пароль не передали — делаем unusable password.
    Это нормальная практика (к примеру: пользователь создан через OAuth).
    """
    test_u = User.objects.create_user(
        email=user_data_default["email"],
        username=user_data_default["username"],
        password=None,
    )
    assert test_u.has_usable_password() is False


@pytest.mark.django_db
def test_create_superuser_success(user_pass_default):
    """
    Проверяем корректность создание superuser
    - флаги staff/superuser = True.
    """
    test_su = User.objects.create_superuser(
        email="test_admin@test.com",
        username="test_admin",
        password=user_pass_default,
    )
    assert test_su.is_staff is True
    assert test_su.is_superuser is True
    assert test_su.check_password(user_pass_default) is True


@pytest.mark.django_db
def test_create_superuser_requires_is_staff_true(user_pass_default):
    """
    Если кто-то пытается создать суперпользователя с is_staff = False — ошибка.
    """
    with pytest.raises(ValueError):
        User.objects.create_superuser(
            email="test_admin2@test.com",
            username="test_admin2",
            password=user_pass_default,
            is_staff=False,
        )


@pytest.mark.django_db
def test_create_superuser_requires_is_superuser_true(user_pass_default):
    """
    Если кто-то пытается создать суперпользователя с is_superuser=False — тоже ошибка.
    """
    with pytest.raises(ValueError):
        User.objects.create_superuser(
            email="test_admin3@example.com",
            username="test_admin3",
            password=user_pass_default,
            is_superuser=False,
        )