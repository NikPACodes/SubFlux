import pytest
from django.contrib.auth import get_user_model

User = get_user_model()

@pytest.fixture()
def user_data():
    """
    Базовые данные тестового пользователя.
    """
    return {
        "email":"test_user1@test.com",
        "username":"test_user1",
        "password":"StrongTestPass123!",
    }

@pytest.fixture()
def user_pass():
    """
    Тестовый пороль
    """
    return "StrongTestPass123!"

@pytest.fixture()
def create_user(db):
    """
    Быстрое создание пользователя в тестах:
    userX = create_user(email="...", username="...", password="...")
    """
    def _create_user(**kwargs):
        return User.objects.create_user(**kwargs)
    return _create_user