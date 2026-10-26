"""
URL-маршруты Справочников.
"""
from django.urls import path, include
from  rest_framework import routers
from .views import CategoryViewSet, CategoryReadViewSet, ProviderViewSet, ProviderReadViewSet

private_router = routers.SimpleRouter()
# Приватные API для ведения
private_router.register(r'categories', CategoryViewSet, basename='admin-categories')
private_router.register(r'providers', ProviderViewSet, basename='admin-providers')


public_router = routers.SimpleRouter()
# Публичные API
public_router.register(r'categories', CategoryReadViewSet, basename='categories')
public_router.register(r'providers', ProviderReadViewSet, basename='providers')

urlpatterns = [
    path('catalog/', include(public_router.urls)),
    path('admin/catalog/', include(private_router.urls)),
]