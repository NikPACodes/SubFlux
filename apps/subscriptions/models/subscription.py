from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models

from .category import Category
from .provider import Provider

from utils.validators import validator_currency, validator_timezone


class Subscription(models.Model):
    """
    Subscription - подписка пользователя.

    Одна запись = одна подписка на конкретный сервис (или созданная вручную)

    Содержит:
    - "состояние" подписки (статус, даты начала/окончания)
    - поля для UI (заметки, метки, платежный метод)
    - денормализацию "Текущей цены" и "Следующего списания" для быстрого поиска
    """

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        PAUSED = "paused", "Paused"
        CANCELED = "canceled", "Canceled"
        TRIAL = "trial", "Trial"
        EXPIRED = "expired", "Expired"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name="subscriptions", db_index=True)
    # Сервис (опционально т.к. запись может быть создана вручную)
    provider = models.ForeignKey(Provider, on_delete=models.SET_NULL,
                                 null=True, blank=True, related_name="subscriptions")
    category = models.ForeignKey(Category, on_delete=models.SET_NULL,
                                 null=True, blank=True, related_name="subscriptions")

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.ACTIVE, db_index=True)

    # Дата начала подписки
    started_at = models.DateField(blank=True, null=True)
    # Дата окончания/отмены подписки
    ended_at = models.DateField(blank=True, null=True)

    # Метод оплаты (текстовое поле для удобства пользователя, НЕ содержит секретных данных
    # Прим: "МИР **** 1234", "PayPal", "VISA" ...
    payment_method_label = models.CharField(max_length=64, blank=True, null=True)
    # Короткая заметка (для удобства пользователя)
    owner_note = models.CharField(max_length=255, blank=True, null=True)
    # Флаг "Делится/общая/семейная подписка" (для аналитики)
    is_shared = models.BooleanField(default=False)

    # Денормализация текущей цены (для удобства запросов)
    current_price_amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])

    # Код валюты (по началу для упрощения Char, в дальнейшем переработается в справочник)
    # ISO 4217 (USD/EUR/RUB...)
    current_price_currency = models.CharField(max_length=3, validators=[validator_currency])

    # Денормализация ближайшего списания (для удобства запросов, истина — BillingSchedule.next_run_at)
    next_billing_at = models.DateTimeField(blank=True, null=True, db_index=True)

    # IANA timezone ("Asia/Yekaterinburg", "Europe/Moscow"...)
    # Используется дял корректного расчета дат списания с учетом локального времени подписки
    billing_timezone = models.CharField(max_length=64, blank=True, null=True, validators=[validator_timezone])

    # Факт последнего списания
    last_billed_at = models.DateTimeField(blank=True, null=True)

    create_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "subscriptions"
        indexes = [
            # Индекс для ускорения поиска подписок пользователя по статусу
            models.Index(fields=["user", "status"]),
            # Индекс для ускорения поиска списка ближайших списаний
            models.Index(fields=["user", "next_billing_at"]),
        ]
        constraints = [
            # Цена не может быть отрицательной
            models.CheckConstraint(condition=models.Q(current_price_amount__gte=0),
                                    name="subscription_current_price_nonnegative"),
        ]

    def __str__(self):
        return self.title