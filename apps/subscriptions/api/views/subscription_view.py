from rest_framework.permissions import IsAuthenticated
from apps.subscriptions.api.permissions import IsOwner
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.viewsets import ModelViewSet
from apps.subscriptions.api.serializers import (SubscriptionSetPriceSerializer,
                                                SubscriptionReadSerializer, SubscriptionCreateSerializer, SubscriptionUpdateSerializer)
from apps.subscriptions.models import Subscription
from rest_framework.response import Response

class SubscriptionViewSet(ModelViewSet):
    """
    API ViewSet для получения/обновления/мягкого удаления данных по подпискам

    Данные подписок доступны только владельцу
    """
    permission_classes = [IsAuthenticated, IsOwner]

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return SubscriptionReadSerializer

        if self.action == 'create':
            return SubscriptionCreateSerializer

        if self.action in ['update', 'partial_update']:
            return SubscriptionUpdateSerializer

        if self.action == 'set_price':
            return SubscriptionSetPriceSerializer

        return SubscriptionReadSerializer


    def get_queryset(self):
        return Subscription.objects.filter(user=self.request.user).select_related('category', 'provider').order_by('-create_at')

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # Внутри serializer вызывается сервисный слой (create_subscription_with_defaults)
        subscription = serializer.save()
        return Response(
            SubscriptionReadSerializer(subscription).data,
            status=status.HTTP_201_CREATED,
        )

    def update(self, request, *args, **kwargs):
        return Response(status=status.HTTP_501_NOT_IMPLEMENTED)

    def partial_update(self, request, *args, **kwargs):
        return Response(status=status.HTTP_501_NOT_IMPLEMENTED)

    def destroy(self, request, *args, **kwargs):
        return Response(status=status.HTTP_501_NOT_IMPLEMENTED)

    @action(detail=True, methods=['post'], url_path='set-price')
    def set_price(self, request, pk=None):
        subscription = self.get_object()

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # Внутри serializer вызывается сервисный слой (set_subscription_price)
        serializer.save(subscription=subscription)
        return Response(
            SubscriptionReadSerializer(subscription).data,
            status=status.HTTP_200_OK,
        )

