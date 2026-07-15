from django.db import IntegrityError, transaction
from apps.workspaces.models import Workspace
from apps.workspaces.utils import gen_ws_code, gen_ws_slug


def create_workspace(*, owner, title: str, workspace_type: str,
                        slug: str|None = None, is_default: bool = False) -> Workspace:
    """
    Сервис для корректного создания Workspace

    Поле Workspace.code должно быть уникальным.
    Генератор gen_ws_code() создаёт случайный код, однако сохраняется небольшая вероятность коллизии.
    Для снижения риска коллизий выполняем дополнительные попытки создания Workspace с новым кодом.
    """
    # Нормализация slug
    normalized_slug = gen_ws_slug(slug or title)

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