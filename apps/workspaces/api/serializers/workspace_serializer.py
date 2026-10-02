from rest_framework import serializers

from apps.workspaces.models import Workspace
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