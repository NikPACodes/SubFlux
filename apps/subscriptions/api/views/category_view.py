from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet
from apps.subscriptions.api.serializers import CategorySerializer, CategoryPublicSerializer
from apps.subscriptions.models import Category

class CategoryViewSet(ModelViewSet):
    """
    API ViewSet для ведения справочника категорий
    """
    permission_classes = [IsAdminUser]
    serializer_class = CategorySerializer
    queryset = Category.objects.all()


class CategoryReadViewSet(ReadOnlyModelViewSet):
    """
    API ViewSet для получения категорий
    """
    permission_classes = [IsAuthenticated]
    serializer_class = CategoryPublicSerializer
    queryset = Category.objects.all()
