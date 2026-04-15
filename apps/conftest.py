import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()

#---------------------- Пользователи ----------------------
@pytest.fixture()
def user_data_default():
    """
    Базовые данные тестового пользователя.
    """
    return {
        "email":"test_user1@test.com",
        "username":"test_user1",
        "password":"StrongTestPass123!",
    }

@pytest.fixture()
def user_pass_default():
    """
    Тестовый пароль
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

@pytest.fixture()
def user_default(db):
    """
    Базовый тестовый пользователь
    """
    return User.objects.create_user(email="test_user1@test.com", username="test_user1", password="StrongTestPass123")


#---------------------- API ----------------------
@pytest.fixture()
def api_client():
    return APIClient()

@pytest.fixture()
def auth_client_default(api_client, user_default):
    """
    Авторизованный базовый пользователь
    """
    api_client.force_authenticate(user=user_default)
    return api_client

@pytest.fixture()
def auth_client_factory():
    """
    Фабрика для получения авторизованных пользователей пользователя в тестах:
    auth_user = auth_client_factory(user="...")
    """
    def _auth_client_factory(user):
        client = APIClient()
        client.force_authenticate(user=user)
        return client
    return _auth_client_factory