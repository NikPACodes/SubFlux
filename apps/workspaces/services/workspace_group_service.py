"""
WorkspaceGroup service

Функционал:
- создание групп
- обновление простых полей группы
- Изменение родительской группы
"""
from apps.workspaces.models import Workspace, WorkspaceGroup
from django.db import transaction
from django.core.exceptions import ValidationError
from utils.generators import gen_slug


def _get_workspace_group_for_update(*,workspace: Workspace, ws_group_id: int) -> WorkspaceGroup:
    """
    Получение WorkspaceGroup с блокировкой
    """
    return WorkspaceGroup.objects.select_for_update().get(id=ws_group_id, workspace=workspace)


@transaction.atomic
def create_workspace_group(*, workspace: Workspace,
                              title: str, slug: str| None = None, description: str="",
                              parent_id: int|None = None,
                              is_active: bool = True) -> WorkspaceGroup:
    """
    Сервис для корректного создания WorkspaceGroup
    """
    parent = None
    if parent_id is not None:
        parent = _get_workspace_group_for_update(workspace=workspace, ws_group_id=parent_id)

    wsg = WorkspaceGroup(workspace=workspace, title=title, slug=gen_slug(slug or title),
                         description=description, parent=parent, is_active=is_active)
    wsg.set_level_from_parent()
    wsg.full_clean()
    wsg.save()

    return wsg


@transaction.atomic
def update_workspace_group(*, workspace: Workspace, ws_group_id: int,
                              title: str|None=None, slug: str|None=None, description: str|None=None,
                              is_active: bool|None=None) -> WorkspaceGroup:
    """
    Обновление простых полей WorkspaceGroup.
    """
    wsg = _get_workspace_group_for_update(workspace=workspace, ws_group_id=ws_group_id)

    if title is not None:
        wsg.title = title

    if slug is not None:
        wsg.slug = gen_slug(slug)

    if description is not None:
        wsg.description = description

    if is_active is not None:
        wsg.is_active = is_active

    wsg.full_clean()
    wsg.save()
    return wsg


@transaction.atomic
def set_workspace_group_parent(*, workspace: Workspace, ws_group_id: int,
                                  new_parent_id: int|None) -> WorkspaceGroup:
    """
    Изменение родительской группы для WorkspaceGroup.
    """
    wsg = _get_workspace_group_for_update(workspace=workspace, ws_group_id=ws_group_id)

    if wsg.children.exists():
        raise ValidationError('Невозможно сменить родительскую группу, т.к. группа сама является родительской')

    new_parent = None
    if new_parent_id is not None:
        new_parent = _get_workspace_group_for_update(workspace=workspace, ws_group_id=new_parent_id)

        if new_parent.pk == wsg.pk:
            raise ValidationError('Группа не может быть parent для себя')

    wsg.parent = new_parent
    wsg.set_level_from_parent()
    wsg.full_clean()
    wsg.save(update_fields=['parent', 'level', 'updated_at'])
    return wsg