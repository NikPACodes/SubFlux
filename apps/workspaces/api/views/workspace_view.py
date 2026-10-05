from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.workspaces.api.serializers import WorkspaceReadSerializer, WorkspaceStatusSerializer
from apps.workspaces.selectors import get_workspace_default
from apps.workspaces.services.workspace_service import set_default_workspace_status
from utils.api.errors import call_service


class DefaultWorkspaceViewSet(viewsets.GenericViewSet):
    """
    API Default Workspace пользователя.

    Доступные операции:
    - получение Default Workspace;
    - изменение статуса Default Workspace (ACTIVE / DEACTIVATED).

    Примечание:
    В OSS доступен только Default Workspace.
    Создание, изменение и удаление Workspace в OSS не поддерживаются.
    """
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return get_workspace_default(user=self.request.user)


    def get_serializer_class(self):
        if self.action == 'status':
            return WorkspaceStatusSerializer

        return WorkspaceReadSerializer


    def list(self, request, *args, **kwargs):
        """
        Получение Default Workspace.

        Метод list() используется, как техническое решение,
        т.к. retrieve() требует привязку к pk.

        По факту метод возвращает карточку 1 объекта.
        """
        workspace = self.get_object()

        serializer = self.get_serializer(workspace)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )


    @action(detail=False, methods=['post'], url_path='status')
    def status(self, request, *args, **kwargs):
        """
        Изменение статуса Default Workspace.
        """
        serializer = self.get_serializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        workspace = call_service(set_default_workspace_status,
                                 user=request.user,
                                 status=serializer.validated_data['status'])

        response_serializer = WorkspaceReadSerializer(workspace)

        return Response(
            response_serializer.data,
            status=status.HTTP_200_OK,
        )