"""
URL-маршруты Subscription.
"""
from  rest_framework import routers
from .views import SubscriptionViewSet

router = routers.SimpleRouter()
router.register(r'subscriptions', SubscriptionViewSet, basename='subscriptions')

urlpatterns = router.urls