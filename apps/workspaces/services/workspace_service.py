"""
Workspace service

Функционал:
- создание рабочего пространства
"""
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from apps.workspaces.models import Workspace
from apps.workspaces.utils import gen_ws_code
from utils.generators import gen_slug
from utils.enums import WorkspaceStatus

@transaction.atomic
def create_workspace(*, owner, title: str, workspace_type: str,
                        slug: str|None = None, is_default: bool = False) -> Workspace:
    """
    Сервис для корректного создания Workspace

    Поле Workspace.code должно быть уникальным.
    Генератор gen_ws_code() создаёт случайный код, однако сохраняется небольшая вероятность коллизии.
    Для снижения риска коллизий выполняем дополнительные попытки создания Workspace с новым кодом.
    """
    # Нормализация slug
    normalized_slug = gen_slug(slug or title)

    last_error: IntegrityError | None = None
    # Для устранения коллизии заложено 5 попыток создания Workspace
    for _ in range(5):
        try:
            with transaction.atomic():
                return Workspace.objects.create(owner=owner, title=title, slug=normalized_slug,
                                                code=gen_ws_code(), type=workspace_type, is_default=is_default)
        except IntegrityError as exc:
            last_error = exc
    raise RuntimeError("Не удалось сгенерировать уникальный код рабочей области после 5 попыток") from last_error


@transaction.atomic
def set_default_workspace_status(*, user, status: str) -> Workspace:
    """
    Изменение статуса Default Workspace.

    Для Default Workspace возможны только переходы:
    - ACTIVE -> DEACTIVATED;
    - DEACTIVATED -> ACTIVE.

    Повторная установка текущего статуса является допустимой
    и не приводит к изменению объекта.
    """

    allowed_statuses = {
        WorkspaceStatus.ACTIVE,
        WorkspaceStatus.DEACTIVATED,
    }

    if status not in allowed_statuses:
        raise ValidationError({"status": "Недопустимый статус Workspace."})

    # Блокируем объект
    workspace = Workspace.objects.select_for_update().get(owner=user, is_default=True)

    # Пользователь не может самостоятельно восстановить Workspace из системного состояния.
    if workspace.status not in allowed_statuses:
        raise ValidationError({"status": f"Изменение Workspace из статуса '{workspace.status}' недоступно."})

    # Идемпотентность:
    # ACTIVE -> ACTIVE или DEACTIVATED -> DEACTIVATED
    if workspace.status == status:
        return workspace

    workspace.status = status
    workspace.save(update_fields=['status',
                                  'updated_at'])

    return workspace