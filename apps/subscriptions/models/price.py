from dataclasses import field

from django.db import models
from django.db.models import Q, F
from django.core.validators import MinValueValidator

from .subscription import Subscription
from .provider import Provider, ProviderLink

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
    source_link = models.ForeignKey(ProviderLink, on_delete=models.SET_NULL,
                                    blank=True, null=True, related_name='verified_price')

    valid_from = models.DateTimeField(db_index=True)
    valid_to = models.DateTimeField(blank=True, null=True)
    is_active = models.BooleanField(default=True, db_index=True)
    update_at = models.DateTimeField(auto_now=True)
    create_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "verified_prices"
        constraints = [
            # Цена не может быть отрицательной
            models.CheckConstraint(condition=Q(amount__gte=0),
                                   name="verified_price_amount_nonnegative", ),
            # Дата начала (valid_from) не может быть позже Дата окончания (valid_to)
            models.CheckConstraint(condition=Q(valid_to__isnull=True) | Q(valid_to__gt=F("valid_from")),
                                   name="verified_price_valid_to_gt_from"),
            # Уникальный ключ VerifiedPrice
            models.UniqueConstraint(
                fields=["provider", "plan_name", "platform", "region", "currency", "period_unit", "period_interval"],
                condition=Q(valid_to__isnull=True),
                name="uniq_active_verified_price",
            ),
        ]
        indexes = [
            models.Index(fields=["provider", "plan_name", "platform", "region", "currency", "period_unit", "period_interval",]),
        ]

    def __str__(self):
        return f"Provider_ID {self.provider_id} -> {self.plan_name} {self.amount} {self.currency} ({self.region})"


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

    verified_price = models.ForeignKey(VerifiedPrice,on_delete=models.PROTECT,
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
            models.CheckConstraint(condition=Q(amount__gte=0),
                                   name="price_history_amount_nonnegative",),
            # Дата начала (effective_from) не может быть позже Дата окончания (effective_to)
            models.CheckConstraint(condition=Q(effective_to__isnull=True) | Q(effective_to__gt=F("effective_from")),
                                   name="price_history_effective_to_gt_from"),
            # Для режима Verified поле verified_price -> обязательное, поля(amount, currency) -> пустые
            # Для режима Manual поля(amount, currency) -> обязательные, поле verified_price -> пустое
            models.CheckConstraint(condition=((Q(verified_price__isnull=False) & Q(amount__isnull=True) & Q(currency__isnull=True)) | # Verified
                                              (Q(verified_price__isnull=True) & Q(amount__isnull=False) & Q(currency__isnull=False)) # Manual
                                              ),
                                    name="price_history_verified_or_manual"),
            # 1 Subscription -> 1 активная PriceHistory
            models.UniqueConstraint(fields=["subscription"],
                                    condition=Q(effective_to__isnull=True),
                                    name="uniq_active_subscription_price")
        ]

    def __str__(self):
        if self.source.VERIFIED:
            return f"Sub_ID {self.subscription_id} -> VerifiedPrice {self.verified_price_amount} {self.verified_price_currency}"
        else:
            return f"Sub_ID {self.subscription_id} -> {self.amount} {self.currency}"