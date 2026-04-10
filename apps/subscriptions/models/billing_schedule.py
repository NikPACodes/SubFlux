from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

from .subscription import Subscription

from utils.enums import PeriodUnit


class BillingSchedule(models.Model):
    """
    BillingSchedule - правила списания + указатель следующего списания

    Содержит:
    - период
    - интервал (каждые N периодов)
    - параметры trial/grace
    - расчетную дату следующего списания next_run_at

    Логика вычисления next_run_at и обновление Subscription.next_billing_at находится в services/
    """

    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE, related_name="billing_schedules")
    period_unit = models.CharField(max_length=8, choices=PeriodUnit.choices)
    # Интервал (каждые N периодов) Прим.: 1 month (каждый месяц), 3 month (каждый квартал), 1 week (каждую неделю) ...
    period_interval = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    # Якорный день месяца (1...31) для month
    anchor_day = models.PositiveSmallIntegerField(blank=True, null=True,
                                                  validators=[MinValueValidator(1), MaxValueValidator(31)])
    # Якорный день недели (0...6) (Mon...Sun) для week
    anchor_weekday = models.PositiveSmallIntegerField(blank=True, null=True,
                                                      validators=[MinValueValidator(0), MaxValueValidator(6)],)

    # Дата окончания пробного периода
    trial_ends_at = models.DateTimeField(blank=True, null=True)
    # Льготный период
    grace_days = models.PositiveSmallIntegerField(default=0)

    # Дата следующего списание
    next_run_at = models.DateTimeField(db_index=True)

    # Актуальность расписания (версионность)
    # При изменении правила - создаем новое is_current=True, старое помечаем False
    is_current = models.BooleanField(default=True, db_index=True)

    create_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "billing_schedules"
        verbose_name = 'График списания'
        verbose_name_plural = 'График списаний'
        indexes = [
            # Быстрое получение актуального расписания
            models.Index(fields=["subscription", "is_current"]),
            # Быстрое получение расписаний по дате списания
            models.Index(fields=["is_current", "next_run_at"]),
        ]
        constraints = [
            # Интервал не может быть меньше 1
            models.CheckConstraint(condition=models.Q(period_interval__gte=1),
                                   name="billing_schedule_interval_gte_1"),
            # 1 Subscription -> 1 актуальное BillingSchedule
            models.UniqueConstraint(fields=["subscription"],
                                    condition=models.Q(is_current=True),
                                    name="uniq_active_subscription_schedule")
        ]

    def __str__(self):
        return f"Sub_ID {self.subscription_id} -> {self.period_interval} {self.period_unit}"