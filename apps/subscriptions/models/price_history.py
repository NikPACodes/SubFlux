from django.core.validators import MinValueValidator
from django.db import models

from .subscription import Subscription


class PriceHistory(models.Model):
    """
    PriceHistory - история изменения цен

    Назначение:
    - Аналитика (рост/снижение цены)
    - Аудит (когда и как менялась цена)
    - Отчеты

    Для быстрого поиска current_price_* хранится в Subscription
    """

    # Источник данных о цене
    class Source(models.TextChoices):
        MANUAL = "manual", "Manual"                # Ручной ввод
        IMPORT = "import", "Import"                # Импорт из файла
        INTEGRATION = "integration", "Integration" # Интеграция

    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE, related_name="price_history")

    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    currency = models.CharField(max_length=3)

    # Дата начала действия
    effective_from = models.DateTimeField(db_index=True)
    # Дата окончания действия
    effective_to = models.DateTimeField(blank=True, null=True)
    # Причина изменения цены
    change_reason = models.CharField(max_length=255, blank=True, null=True)
    # Источник данных
    source = models.CharField(max_length=16, choices=Source.choices, default=Source.MANUAL)

    create_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "price_history"
        indexes = [
            # Быстрое получение последней цены по подписке
            models.Index(fields=["subscription", "-effective_from"]),
        ]
        constraints = [
            # Цена не может быть отрицательной
            models.CheckConstraint(condition=models.Q(amount__gte=0),
                                   name="price_history_amount_nonnegative",),
            # Дата начала (effective_from) не может быть позже Дата окончания (effective_to)
            models.CheckConstraint(condition=models.Q(effective_to__isnull=True) | models.Q(effective_to__gt=models.F("effective_from")),
                                   name="price_history_effective_to_gt_from",),
        ]

    def __str__(self):
        return f"{self.subscription__id}: {self.amount} {self.currency}"