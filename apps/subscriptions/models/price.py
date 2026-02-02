from django.db import models
from django.core.validators import MinValueValidator

from . import ProviderLink
from .subscription import Subscription
from .provider import Provider

from utils.validators import validator_currency, validator_region
from utils.enums import VerifiedPriceSource, PriceHistorySource, Platform, PeriodUnit

class VerifiedPrice(models.Model):
    """
    VerifiedPrice — доверенная (подтверждённая) цена тарифа провайдера.

    Это прайс-лист/тарифная сетка обновляемая:
    - админом,
    - API,
    - синхронизацией.

    Важный принцип: изменение VerifiedPrice НЕ переписывает историю пользователей,
    а создаёт новые интервалы в PriceHistory для будущего.
    """

    provider = models.ForeignKey(Provider, on_delete=models.CASCADE, related_name='verified_price')
    plan_name = models.CharField(max_length = 128, blank=True, null=True)

    # Регион поле Char с соответствием формату:
    # ISO 3166-1 alpha-2 (US, DE, RU, ...) или GLOBAL
    region = models.CharField(max_length=8, default="GLOBAL", validators=[validator_region], db_index=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    currency = models.CharField(max_length=3, validators=[validator_currency])
    # Единица периода
    period_unit = models.CharField(max_length=8, choices=PeriodUnit.choices)
    # Количество периодов
    period_interval = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])

    platform = models.CharField(max_length=10, choices=Platform.choices, default=Platform.WEB, db_index=True)
    # Источник данных
    source = models.CharField(max_length=8, choices=VerifiedPriceSource.choices)
    source_link = models.ForeignKey(ProviderLink, on_delete=models.CASCADE, related_name='verified_price')

    valid_from = models.DateTimeField(db_index=True)
    valid_to = models.DateTimeField(blank=True, null=True)
    is_active = models.BooleanField(default=True, db_index=True)
    update_at = models.DateTimeField(auto_now=True)
    create_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "verified_prices"
        constraints = [
            models.UniqueConstraint(
                fields=["provider", "region", "currency", "plan_name", "valid_from"],
                name="verified_price_version",
            ),
        ]
        indexes = [
            models.Index(fields=["provider", "region", "currency", "plan_name"]),
        ]

    def __str__(self):
        return f"{self.provider}:{self.plan_name} {self.amount} {self.currency} ({self.region})"


class PriceHistory(models.Model):
    """
    PriceHistory — история цены конкретной пользовательской подписки.

    Два режима:
    1) Verified mode:
       - verified_price заполнен
       - amount/currency пустые
    2) Manual mode:
       - amount/currency заполнены
       - verified_price пустой

    Назначение:
    - Аналитика (рост/снижение цены)
    - Аудит (когда и как менялась цена)
    - Отчеты

    История хранится интервалами:
    - effective_from — когда цена начала действовать
    - effective_to — когда перестала (NULL = активная)

    Для быстрого поиска current_price_* хранится в Subscription
    """

    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE, related_name="price_history")

    verified_price = models.ForeignKey(VerifiedPrice,on_delete=models.SET_NULL,
                                       blank=True, null=True, related_name="price_history")

    amount = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True,
                                 validators=[MinValueValidator(0)], help_text="Заполняется только для manual-режима.",)
    currency = models.CharField(max_length=3, blank=True, null=True,
                                validators=[validator_currency], help_text="Заполняется только для manual-режима.",)

    # Дата начала действия
    effective_from = models.DateTimeField(db_index=True)
    # Дата окончания действия
    effective_to = models.DateTimeField(blank=True, null=True)
    # Причина изменения цены
    change_reason = models.CharField(max_length=255, blank=True, null=True)
    # Источник данных о цене
    source = models.CharField(max_length=16, choices=PriceHistorySource.choices, default=PriceHistorySource.MANUAL)

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
                                   name="price_history_effective_to_gt_from"),
        ]

    def __str__(self):
        if self.source.VERIFIED:
            return f"{self.subscription__title} ({self.subscription__id}): {self.verified_price__amount} {self.verified_price__currency}"
        else:
            return f"{self.subscription__title} ({self.subscription__id}): {self.amount} {self.currency}"