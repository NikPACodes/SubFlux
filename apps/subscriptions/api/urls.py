from django.urls import path, include
from  rest_framework import routers
from .views import CategoryViewSet, CategoryReadViewSet, ProviderViewSet, ProviderReadViewSet, SubscriptionViewSet

router = routers.DefaultRouter()
router.register(r'admin/categories', CategoryViewSet, basename='admin-categories')
router.register(r'categories', CategoryReadViewSet, basename='categories')
router.register(r'admin/providers', ProviderViewSet, basename='admin-providers')
router.register(r'providers', ProviderReadViewSet, basename='providers')
router.register(r'subscriptions', SubscriptionViewSet, basename='subscriptions')

urlpatterns = [
    path('', include(router.urls)),
]