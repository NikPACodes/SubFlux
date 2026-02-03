from django.urls import path, include
from  rest_framework import routers
from .views import SubscriptionViewSet

router = routers.DefaultRouter()
router.register(r'subscriptions', SubscriptionViewSet, basename='subscriptions')

urlpatterns = [
    path('', include(router.urls)),
]