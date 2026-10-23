from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from apps.subscriptions.api.serializers import (SubscriptionSetPriceSerializer,
                                                SubscriptionSetStatusSerializer, SubscriptionCancelSerializer,
                                                SubscriptionReadSerializer, SubscriptionCreateSerializer, SubscriptionUpdateSerializer)
from apps.subscriptions.models import Subscription
from apps.subscriptions.services.subscription_service import set_subscription_status
from apps.workspaces.models import Workspace
from apps.workspaces.selectors import get_workspace_default

from utils.enums import SubscriptionStatus
from utils.api.errors import call_service

#---------------------------------------------------------------------------------

class SubscriptionViewSet(ModelViewSet):
    """
    API ViewSet для получения/обновления/мягкого удаления данных по подпискам
    """
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        """
        Все serializers должны возвращать Subscription
        """
        if self.action in ['list', 'retrieve']:
            return SubscriptionReadSerializer

        if self.action == 'create':
            return SubscriptionCreateSerializer

        if self.action in ['update', 'partial_update']:
            return SubscriptionUpdateSerializer

        if self.action == 'set_price':
            return SubscriptionSetPriceSerializer

        if self.action == 'set_status':
            return SubscriptionSetStatusSerializer

        if self.action == 'cancel':
            return SubscriptionCancelSerializer

        return SubscriptionReadSerializer


    def get_workspace(self) -> Workspace:
        """
        Получаем Workspace пользователя.

        Примечание:
        - в OSS поддерживается работа только с Default Workspace пользователя.
        """
        if not hasattr(self, '_workspace'):
            self._workspace = get_workspace_default(user=self.request.user)
        return self._workspace


    def get_serializer_context(self):
        context = super().get_serializer_context()
        # Передаём Workspace в контекст сериализатора при создании Subscription.
        # Для остальных операций Workspace определяется через существующую Subscription.
        if self.action == 'create':
            context['workspace'] = self.get_workspace()
        return context


    def get_queryset(self):
        """
        Получаем Subscription по Workspace.
        """
        return (Subscription.objects.filter(workspace=self.get_workspace(), is_deleted=False)
                                    .select_related('workspace', 'ws_group', 'category', 'provider')
                                    .order_by('-create_at'))


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
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        # Внутри serializer вызывается сервисный слой (update_subscription_data)
        subscription = serializer.save()
        return Response(
            SubscriptionReadSerializer(subscription).data,
            status=status.HTTP_200_OK,
        )


    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)


    def destroy(self, request, *args, **kwargs):
        return Response(status=status.HTTP_501_NOT_IMPLEMENTED)


    @action(detail=True, methods=['post'], url_path='set-price')
    def set_price(self, request, pk=None):
        subscription = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # Внутри serializer вызывается сервисный слой (set_subscription_price)
        subscription = serializer.save(subscription=subscription)
        return Response(
            SubscriptionReadSerializer(subscription).data,
            status=status.HTTP_200_OK,
        )


    @action(detail=True, methods=['post'], url_path='set-status')
    def set_status(self, request, pk=None):
        subscription = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # Внутри serializer вызывается сервисный слой (set_subscription_status)
        subscription = serializer.save(subscription=subscription)
        return Response(
            SubscriptionReadSerializer(subscription).data,
            status=status.HTTP_200_OK,
        )


    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        subscription = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # Внутри serializer вызывается сервисный слой (set_subscription_status)
        subscription = serializer.save(subscription=subscription)
        return Response(
            SubscriptionReadSerializer(subscription).data,
            status=status.HTTP_200_OK,
        )


    @action(detail=True, methods=['post'])
    def pause(self, request, pk=None):
        subscription = self.get_object()
        if subscription.status != SubscriptionStatus.ACTIVE:
            raise ValidationError({"status": "Приостановка доступна только для действующих (активных) подписок."})

        subscription = call_service(
                           set_subscription_status,
                           subscription=subscription,
                           status_new=SubscriptionStatus.PAUSED
                        )

        return Response(
            SubscriptionReadSerializer(subscription).data,
            status=status.HTTP_200_OK,
        )


    @action(detail=True, methods=['post'])
    def resume(self, request, pk=None):
        subscription = self.get_object()
        if subscription.status != SubscriptionStatus.PAUSED:
            raise ValidationError({"status": "Возможно возобновить только приостановленную подписку."})

        subscription = call_service(
                           set_subscription_status,
                           subscription=subscription,
                           status_new=SubscriptionStatus.ACTIVE
                           )

        return Response(
            SubscriptionReadSerializer(subscription).data,
            status=status.HTTP_200_OK,
        )

    # @action(detail=True, methods=['post'], url_path='set-provider')
    # def set_provider(self, request, pk=None):
    #     pass