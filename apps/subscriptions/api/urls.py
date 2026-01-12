from django.urls import path, include
from  rest_framework import routers
from .views import SubscriptionViewSet

routers = routers.DefaultRouter()
routers.register(r'subscriptions', SubscriptionViewSet, basename='subscriptions')

urlpatterns = [
    path('', include(routers.urls)),
]