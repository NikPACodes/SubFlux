from apps.subscriptions.models import Subscription
from rest_framework import serializers

class SubscriptionSerializer(serializers.ModelSerializer):
    """
    Сериализатор подписки

    next_billing_at/last_billed_at - расчетные поля, поэтому только read_only
    """
    class Meta:
        model = Subscription
        fields = [
            'id',
            'title',
            'description',
            'status',
            'provider',               # Сервис/Провайдер
            'category',
            'started_at',             # Дата начала подписки
            'ended_at',               # Дата окончания/отмены подписки
            'payment_method_label',   # Метод оплаты (текст)
            'owner_note',             # Короткая заметка
            'is_shared',              # Флаг "Делится/общая/семейная подписка"
            'current_price_amount',   # Текущая цена
            'current_price_currency', # Код валюты
            'next_billing_at',        # Дата ближайшего списания
            'billing_timezone',       # IANA timezone
            'last_billed_at',         # Факт последнего списания
            'create_at',
            'update_at',
        ]
        read_only_fields = [
            'id',
            'next_billing_at',
            'last_billed_at',
            'create_at',
            'update_at',
        ]