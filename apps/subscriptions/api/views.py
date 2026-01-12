from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet
from .serializers import SubscriptionSerializer
from apps.subscriptions.models import Subscription

class SubscriptionViewSet(ModelViewSet):
    """
    API ViewSet для подписок

    Важно:
    - queryset ограничен текущим пользователем
    - создание привязывается к request.user
    """
    permission_classes = [IsAuthenticated]
    serializer_class = SubscriptionSerializer

    def get_queryset(self):
        return Subscription.objects.filter(user=self.request.user).select_related('provider', 'category')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)