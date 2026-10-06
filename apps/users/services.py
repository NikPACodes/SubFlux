from django.contrib.auth import get_user_model
from django.db import transaction

from apps.workspaces.services.workspace_service import create_workspace
from utils.enums import WorkspaceType


User = get_user_model()

@transaction.atomic
def register_user(*, email: str, username: str, password: str | None = None,
                  first_name: str | None = None, last_name: str | None = None,
                  phone: str | None = None, bio: str = None, gender: str = "U", birth_date = None) -> User:
    """
    Сценарий регистрации (создания) пользователя
    Вместе с пользователем создаётся Default Workspace.

    Назначение:
    - вынос бизнес-логики из DRF
    - регистрация через email+password
    - регистрация через allauth
    - регистрация через OTP
    """

    # Используем manager.create_user для (корректного хэш пароля)
    user = User.objects.create_user(email=email, username=username, password=password)

    user.first_name = first_name
    user.last_name = last_name
    user.phone = phone
    user.bio = bio
    user.gender = gender
    user.birth_date = birth_date

    user.save()

    # Создаём Default Workspace
    create_workspace(owner=user, title=username, slug=username,
                     workspace_type=WorkspaceType.PERSONAL, is_default=True)

    return user