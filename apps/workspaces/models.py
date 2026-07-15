from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from utils.enums import WorkspaceType, WorkspaceStatus
from django.conf import settings
from apps.workspaces.utils import gen_ws_code

class Workspace(models.Model):
    """
    Workspace - Рабочее пространство

    Основной контейнер данных в SubFlux.

    Workspace отвечает за:
    - владение подписками;
    - изоляцию данных между пользователями и командами;
    - участников и их роли;
    - статус доступности;
    - аналитику, уведомления и аудит.
    """
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=64, db_index=True)
    description = models.TextField(blank=True)

    # Уникальный код для определения workspace
    # Необходим для дла разграничения Workspace с одинаковым slug, но разными owners
    code = models.CharField(max_length=16, unique=True, editable=False,
                            default=gen_ws_code, db_index=True)
    type = models.CharField(max_length=32, choices=WorkspaceType.choices,
                            default=WorkspaceType.PERSONAL, db_index=True)
    status = models.CharField(max_length=16, choices=WorkspaceStatus.choices,
                              default=WorkspaceStatus.ACTIVE, db_index=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
                              related_name='owned_workspaces')
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'workspaces'
        verbose_name = 'Рабочее пространство'
        verbose_name_plural = 'Рабочие пространства'
        indexes = [
            # Индекс для ускорения поиска по статусу (активные personal/team)
            models.Index(fields=['status', 'type'],
                         name='ws_status_type_idx'),
            # Индекс для ускорения поиска workspaces владельца
            models.Index(fields=['owner', 'status'],
                         name='ws_owner_status_idx'),
            # Индекс для служебных выборок: активные, удаленные и т.д.
            models.Index(fields=['status', 'created_at'],
                         name='ws_status_created_idx'),
        ]

        constraints = [
            # Поля Title Slug Code не могут быть пустыми
            models.CheckConstraint(condition = ~models.Q(title='') & ~models.Q(slug='') & ~models.Q(code=''),
                                   name='ws_title_slug_code_not_empty'),


            models.CheckConstraint(condition=(models.Q(is_default=False) | models.Q(type=WorkspaceType.PERSONAL)),
                                   name='ws_default_must_be_personal'),

            # Возможен лишь 1 личный (default) Workspace
            models.UniqueConstraint(fields=['owner'],
                                    condition=(models.Q(is_default=True) & models.Q(type=WorkspaceType.PERSONAL)),
                                    name='uniq_ws_default_per_owner'),
            # Workspace Slug уникален для владельца
            models.UniqueConstraint(fields=('owner', 'slug'),
                                    name='uniq_ws_owner_slug'),
        ]

    def __str__(self) -> str:
        return f"{self.title} ({self.code})"



class WorkspaceGroup(models.Model):
    """
    Пользовательские группировки Subscriptions

    Примеры:
    - личные группировки;
    - подразделения;
    - отделы;
    - области применения.
    """
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='groups')

    title = models.CharField(max_length=255, db_index=True)
    slug = models.SlugField(max_length=64, db_index=True)
    description = models.TextField(blank=True)

    # Уровень вложенности. Максимальный уровень - 3)
    level = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1), MaxValueValidator(3)])
    parent = models.ForeignKey('self', on_delete=models.PROTECT, null=True, blank=True, related_name='children')

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'workspace_groups'
        verbose_name = 'Группа / Отдел / Подразделение'
        verbose_name_plural = 'Группы / Отделы / Подразделения'
        ordering = ['workspace', 'level']
        indexes = [
            # Основная выборка групп Workspace
            models.Index(fields=['workspace', 'is_active'],
                         name='wsg_ws_is_active_idx'),
            # Получение групп по уровню
            models.Index(fields=['workspace', 'level', 'is_active'],
                         name='wsg_ws_level_is_active_idx'),
            # Получение дочерних групп
            models.Index(fields=['parent', 'is_active'],
                         name='wsg_parent_is_active_idx'),
            # Фильтры по slug / title
            models.Index(fields=['workspace', 'slug'],
                         name='wsg_ws_slug_idx'),
            models.Index(fields=['workspace', 'title'],
                         name='wsg_ws_title_idx'),
        ]
        constraints = [
            # Поля Title Slug не могут быть пустыми
            models.CheckConstraint(condition=(~models.Q(title='') & ~models.Q(slug='')),
                                   name='wsg_title_slug_not_empty'),
            # Parent обязателен и появляется только для level > 1
            models.CheckConstraint(condition=(models.Q(parent__isnull=True, level=1) | models.Q(parent__isnull=False, level__gt=1)),
                                   name='wsg_parent_level_consistency'),
            # Группа не может ссылаться сама на себя
            models.CheckConstraint(condition=~models.Q(parent=models.F('id')),
                                   name='wsg_parent_not_self'),

            # Slug корневой группы уникален
            models.UniqueConstraint(fields=['workspace', 'slug'],
                                    condition=models.Q(parent__isnull=True),
                                    name='uniq_wsg_root_slug'),
            # Slug дочерней группы уникален
            models.UniqueConstraint(fields=['parent', 'slug'],
                                    condition=models.Q(parent__isnull=False),
                                    name='uniq_wsg_child_slug'),
        ]

    def __str__(self):
        return f'Workspace_ID {self.workspace_id} -> {self.title} {self.level}'
