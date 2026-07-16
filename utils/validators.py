from django.core.exceptions import ValidationError
from django.utils import timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
import re
from pycountry import currencies, countries
from decimal import Decimal
from typing import Optional, Any

from utils.enums import PriceHistorySource, PeriodUnit, SubscriptionStatus

_CURRENCY_RE = re.compile(r'^[A-Z]{3}$')   # ISO 4217 (USD/EUR/RUB...)
_COUNTRY_RE = re.compile(r'^[A-Z]{2}$')    # ISO 3166-1 alpha-2 (US, DE, RU, ...) или GLOBAL

_ALLOWED_STATUS = {
    SubscriptionStatus.TRIAL: (SubscriptionStatus.ACTIVE, SubscriptionStatus.EXPIRED),
    SubscriptionStatus.DELAYED: (SubscriptionStatus.ACTIVE,),
    SubscriptionStatus.ACTIVE: (SubscriptionStatus.PAUSED, SubscriptionStatus.CANCELED, SubscriptionStatus.EXPIRED),
    SubscriptionStatus.PAUSED: (SubscriptionStatus.ACTIVE, ),
    SubscriptionStatus.CANCELED: (SubscriptionStatus.EXPIRED, SubscriptionStatus.ACTIVE),
    SubscriptionStatus.EXPIRED: (SubscriptionStatus.DELAYED, SubscriptionStatus.ACTIVE),
}


def validator_timezone(value: str, allow_empty: bool = False) -> None:
    """
    Валидация IANA timezone ("Asia/Yekaterinburg", "Europe/Moscow"...)
    """
    if value in (None, ''):
        if allow_empty:
            return
        raise ValidationError(f'Timezone не может быть пустой')

    try:
        ZoneInfo(value)
    except ZoneInfoNotFoundError as e:
        raise ValidationError(f'Некорректная IANA timezone: {value}') from e


def validator_currency(value: str) -> None:
    """
    Валидация валюты ISO 4217 (USD/EUR/RUB...)
    """
    if value in (None, ''):
        raise ValidationError(f'Код валюты обязателен для заполнения')

    # Проверка соответствия формату ISO 4217 alpha-3
    if not _CURRENCY_RE.match(value):
        raise ValidationError(f'Код валюты не соответствует формату ISO 4217')

    if currencies.get(alpha_3=value) is None:
        raise ValidationError(f'Валюта не найдена: {value}')


def validator_region(value: str) -> None:
    """
    Валидация региона ISO 3166-1 alpha-2 (US, DE, RU, ...) или GLOBAL
    """
    if value in (None, ''):
        raise ValidationError(f'Регион обязателен для заполнения')

    if value == 'GLOBAL':
        return

    # Проверка соответствия формату ISO 3166-1 alpha-2
    if not _COUNTRY_RE.match(value):
        raise ValidationError(f'Регион не соответствует формату ISO 3166-1 alpha-2 или GLOBAL')

    if countries.get(alpha_2=value) is None:
        raise ValidationError(f'Регион не найден: {value}')


def validator_price_history_source(*, source: str, verified_price = None,
                                      amount: Optional[Decimal] = None, currency: Optional[str] = None) -> None:
    """
    Валидация корректности режимов источника цены для PriceHistory
    Manual: Обязательное заполнение полей -> amount, current. Поле verified_price не учитывается.
    Verified: Обязательное заполнение поля -> verified_price. Поля amount, current не учитываются.
    """
    if source == PriceHistorySource.VERIFIED:
        if not verified_price:
            raise ValidationError("Verified: verified_price не может отсутствовать")
        if amount is not None or currency is not None:
            raise ValidationError("Verified: amount и currency должны быть пустыми")
    elif source == PriceHistorySource.MANUAL:
        if amount is None:
            raise ValidationError("Manual: amount обязательное к заполнению")
        if amount <= 0:
            raise ValidationError("Цена (amount) не может быть отрицательной.")
        if not currency:
            raise ValidationError("Manual: currency обязательное к заполнению")
        if verified_price:
            raise ValidationError("Manual: verified_price должна быть пустой")
    else:
        raise ValidationError("Некорректный источник цены (price.source). Поддерживаются verified/manual режимы")


def validator_billing_schedule_params(*, period_unit: str, period_interval: int, anchor_day: Optional[int],
                                         anchor_weekday: Optional[int], grace_days: int) -> None:
    """
    Валидация расписания “по смыслу”.

    Назначение:
    - Проверка логических зависимостей
        * поле anchor_day обязательно для MONTH (BillingSchedule.period_unit)
        * поле anchor_weekday обязательно для WEEK (BillingSchedule.period_unit)
        * для DAY/YEAR нет поля якоря
        * проверка интервалов
    """
    if period_interval < 1:
        raise ValidationError("Интервал (каждые N периодов) должен быть >= 1")

    if grace_days < 0:
        raise ValidationError("Льготный период должен быть >= 0")

    if period_unit == PeriodUnit.MONTH and anchor_day is None:
        raise ValidationError("anchor_day является обязательным для интервала (period_unit) по месяцам (MONTH)")
    elif period_unit == PeriodUnit.WEEK and anchor_weekday is None:
        raise ValidationError("anchor_weekday является обязательным для интервала (period_unit) по неделям (WEEK)")


def validator_subscription_status(*, status: str, started_at, ended_at = None, trial_ends_at = None, now = None) -> None:
    """
    Валидация состояний подписки

    TRIAL -> Пробный период
        * started_at <= Текущей даты
        * ended_at - Пуст
        * trial_ends_at > Текущей даты
    DELAYED -> Отложенное начало подписки
        * started_at > Текущей даты
        * ended_at - Пуст
    ACTIVE -> Активная подписка
        * started_at <= Текущей даты
        * ended_at - Пуст
    PAUSED -> Приостановлена
        * started_at <= Текущей даты
        * ended_at - Пуст
    CANCELED -> Отменена, но ещё активна
        * started_at <= Текущей даты
        * ended_at > Текущей даты
    EXPIRED -> Отменена
        * started_at <= ended_at
        * ended_at <= Текущей даты
    """
    now = now or timezone.now()

    if started_at is None:
        raise ValidationError("Дата начала (started_at) не может быть пустой")

    if started_at > now and status != SubscriptionStatus.DELAYED:
        raise ValidationError("Дата начала (started_at) не должна превышать текущую")

    if ended_at is not None and started_at > ended_at:
        raise ValidationError("Дата начала (started_at) не может превышать дату окончания (ended_at)")


    if status == SubscriptionStatus.TRIAL:
        if ended_at is not None:
            raise ValidationError("TRIAL: Дата окончания (ended_at) должна быть пустой")
        if trial_ends_at is None:
            raise ValidationError("TRIAL: Дата окончания пробного периода (trial_ends_at) не может быть пустой")
        if trial_ends_at <= now:
            raise ValidationError("TRIAL: Дата окончания пробного периода (trial_ends_at) должна быть больше текущей даты")

    elif status == SubscriptionStatus.DELAYED:
        if started_at <= now:
            raise ValidationError("DELAYED: Дата начала (started_at) должна быть больше текущей даты")
        if ended_at is not None:
            raise ValidationError("DELAYED: Дата окончания (ended_at) должна быть пустой")

    elif status == SubscriptionStatus.ACTIVE:
        if ended_at is not None:
            raise ValidationError("ACTIVE: Дата окончания (ended_at) должна быть пустой")

    elif status == SubscriptionStatus.PAUSED:
        if ended_at is not None:
            raise ValidationError("PAUSED: Дата окончания (ended_at) должна быть пустой")

    elif status == SubscriptionStatus.CANCELED:
        if ended_at is None:
            raise ValidationError("CANCELED: Дата окончания (ended_at) обязательна к заполнению")
        if ended_at <= now:
            raise ValidationError("CANCELED: Дата окончания (ended_at) должна быть больше текущей даты")

    elif status == SubscriptionStatus.EXPIRED:
        if ended_at is None:
            raise ValidationError("EXPIRED: Дата окончания (ended_at) обязательна к заполнению")
        if ended_at > now:
            raise ValidationError("EXPIRED: Дата окончания (ended_at) не может превышать текущую")

    else:
        raise ValidationError("Некорректный статус подписки")


def validator_subscription_status_change(status_current: str, status_new: str) -> None:
    """
    Валидация смены статусов в подписке
    (для корректного соблюдения жизненного цикла подписки)

    Жизненный цикл подписки:
    TRIAL   --> ACTIVE / EXPIRED
    DELAYED --> ACTIVE --> PAUSED   --> ACTIVE
                       --> CANCELED --> EXPIRED / ACTIVE
                       --> EXPIRED  --> DELAYED / ACTIVE
    """
    if status_current == status_new:
        return

    allowed_status = _ALLOWED_STATUS.get(status_current)
    if allowed_status is None or status_new not in allowed_status:
        raise ValidationError(f"Переход из статуса {status_current} в статус {status_new} запрещён")


def validator_tree_integrity(*, instance: Any, parent_attr: str = 'parent', level_attr: str = 'level',
                                workspace_id_attr: str = 'workspace_id', max_depth: int = 3) -> None:
    """
    Валидация корректности структуры дерева.

    Проверки:
    - root должен иметь level = 1;
    - child должен иметь level = parent.level + 1;
    - parent и child должны принадлежать одному workspace;
    - узел не может быть parent самому себе;
    - нельзя создать циклическую вложенность;
    - глубина дерева не должна превышать max_depth.
    """
    if max_depth < 1:
        raise ValidationError(f"Максимальный уровень вложенности дерева должен быть >= 1.")

    # Получение значений
    parent = getattr(instance, parent_attr, None)
    level = getattr(instance, level_attr, None)
    ws_id = getattr(instance, workspace_id_attr, None)

    if level is None:
        raise ValidationError(f"Уровень дерева не может быть пустым.")
    elif level < 1:
        raise ValidationError(f"Уровень дерева должен быть >= 1.")
    elif level > max_depth:
        raise ValidationError(f"Максимальный уровень вложенности {max_depth}.")

    # Если parent отсутствует, значит это root.
    if parent is None:
        if level != 1:
            raise ValidationError(f"Корневой узел должен иметь уровень 1.")
        return

    # Parent не сохранен (нет pk).
    if getattr(parent, "pk", None) is None:
        raise ValidationError(f"Не получилось получить PK parent")

    if instance.pk and parent.pk == instance.pk:
        raise ValidationError(f"Узел не может ссылаться на себя.")

    # Получение Workspace ID родителя
    parent_ws_id = getattr(parent, workspace_id_attr, None)

    if parent_ws_id != ws_id:
        raise ValidationError(f"Workspace родителя не соответствует Workspace текущего узла.")

    parent_level = getattr(parent, level_attr, None)
    if parent_level is None:
        raise ValidationError(f"Уровень родительского узла не определен.")

    # Ожидаемый уровень
    next_level = parent_level + 1
    if level != next_level:
        raise ValidationError(f"Уровень не корректен {level}. Ожидаемый уровень {next_level}.")

    # Проверка корректность вложенности дерева вверх
    ancestor = parent
    #
    visited_ids = set()
    # Подымаемся по дереву
    while ancestor is not None:
        ancestor_pk = getattr(ancestor, "pk", None)

        if ancestor_pk is not None:
            if ancestor_pk in visited_ids:
                raise ValidationError(f"Циклическая вложенность в дерево не допускается.")
            visited_ids.add(ancestor_pk)

        if instance.pk and ancestor_pk == instance.pk:
            raise ValidationError(f"Циклическая вложенность в дерево не допускается.")

        ancestor_ws_id = getattr(ancestor, workspace_id_attr, None)

        if ancestor_ws_id != ws_id:
            raise ValidationError(f"Все предки должны принадлежать одному Workspace.")
        # Получение следующего предка
        ancestor = getattr(ancestor, parent_attr, None)