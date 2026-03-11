from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet
from apps.subscriptions.api.serializers import ProviderSerializer, ProviderPublicSerializer
from apps.subscriptions.models import Provider

class ProviderViewSet(ModelViewSet):
    """
    API ViewSet для ведения справочника провайдеров (сервисов)
    """
    permission_classes = [IsAdminUser]
    serializer_class = ProviderSerializer
    queryset = Provider.objects.all()


class ProviderReadViewSet(ReadOnlyModelViewSet):
    """
    API ViewSet для получения провайдеров (сервисов)
    """
    permission_classes = [IsAuthenticated]
    serializer_class = ProviderPublicSerializer
    queryset = Provider.objects.filter(is_active=True)
