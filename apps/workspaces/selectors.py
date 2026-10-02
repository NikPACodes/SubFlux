"""
Селекторы Workspaces.

Содержат логику получения Workspace:
- default workspace пользователя

Примечание: в OSS проекта поддерживается работа только с Default Workspace пользователя.
Работа с дополнительными Workspace, не входит в функциональность OSS.
"""
from apps.workspaces.models import Workspace


def get_workspace_default(*, user) -> Workspace:
    """
    Получаем Default Workspace пользователя.
    - is_default=True
    - существует всегда
    - только в 1 экземпляре
    """
    return Workspace.objects.get(owner=user, is_default=True)