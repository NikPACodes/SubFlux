from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone
from .subscription import Subscription
from .price import PriceHistory

from utils.enums import PaymentSource
from utils.validators import validator_currency


class Payment(models.Model):
    """
    Payment — факт списания.

    Это НЕ обработка платежей и НЕ хранение реквизитов.
    Только учёт события списания (сумма/валюта/дата) + источник.
    """

    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE, related_name="payments")

    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    currency = models.CharField(max_length=3, validators=[validator_currency])

    paid_at = models.DateTimeField(default=timezone.now)
    source = models.CharField(max_length=16, choices=PaymentSource.choices, default=PaymentSource.MANUAL)

    # Опционально: снимок привязки к "какая цена действовала" (удобно для аудита)
    price_history = models.ForeignKey(PriceHistory, on_delete=models.SET_NULL,
                                      blank=True,  null=True, related_name="payments")

    note = models.CharField(max_length=255, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-paid_at", "-created_at"]
        indexes = [
            models.Index(fields=["subscription", "paid_at"]),
        ]

    def __str__(self):
        return f"{self.subscription__title} ({self.subscription__id}), {self.amount} {self.currency}, at={self.paid_at})"