from rest_framework import serializers

from apps.workspaces.models import Workspace
from apps.workspaces.services.workspace_service import set_default_workspace_status
from utils.api.errors import call_service
from utils.enums import WorkspaceStatus


class WorkspaceReadSerializer(serializers.ModelSerializer):
    """
    Сериализатор для получения Default Workspace пользователя.
    """
    class Meta:
        model = Workspace
        fields = [
            'id',
            'code',
            'slug',
            'title',
            'description',
            'type',
            'status',
            'is_default',
            'timezone',
            'created_at',
            'updated_at',
        ]

        read_only_fields = fields


class WorkspaceStatusSerializer(serializers.Serializer):
    """
    Сериализатор для изменения статуса Default Workspace.

    Пользователю OSS доступны только:
    - ACTIVE;
    - DEACTIVATED.
    """
    status = serializers.ChoiceField(choices=[WorkspaceStatus.ACTIVE,
                                              WorkspaceStatus.DEACTIVATED],
                                     required=True)

    def save(self, *, user):
        return call_service(
            set_default_workspace_status,
            user=user,
            status=self.validated_data['status']
        )