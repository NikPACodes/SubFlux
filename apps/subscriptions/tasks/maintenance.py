from django.db import transaction
from django.utils import timezone

from apps.subscriptions.models import BillingSchedule
from apps.subscriptions.services.billing_service import recalculate_schedule_next_run, sync_subscription_next_billing


@transaction.atomic
def recalculate_due_schedules(limit: int = 500) -> int:
    """
    Задача по пересчету расписания и синхронизации Subscription.next_billing_at

    Сейчас вызывается вручную или через management command.
    В будущем — оборачивается в Celery task без изменения логики.
    """
    now = timezone.now()

    # находит расписания, у которых next_run_at <= now
    schedules = BillingSchedule.objects.select_related("subscription").filter(is_current=True, next_run_at__lte=now).order_by("next_run_at")[:limit]

    processed = 0
    for schedule in schedules:
        # Пересчитываем schedule.next_run_at
        recalculate_schedule_next_run(schedule, from_dt=now)
        # Синхронизируем Subscription.next_billing_at
        sync_subscription_next_billing(schedule.subscription)
        processed += 1

    return processed