from rest_framework import serializers
from apps.subscriptions.models import Provider

class ProviderSerializer(serializers.ModelSerializer):
    """
    Сериализатор для CRUD по справочнику провайдеров
    """
    class Meta:
        model = Provider
        fields = [
            'id',
            'name',
            'slug',
            'description',
            'logo_url',
            'last_links_checked_at',
            'is_active',
            'update_at',
            'create_at',
        ]

        read_only_fields = [
            'id',
            'last_links_checked_at',
            'update_at',
            'create_at',
        ]


class ProviderPublicSerializer(serializers.ModelSerializer):
    """
    Публичный сериализатор для получения провайдера
    """
    class Meta:
        model = Provider
        fields = [
            'id',
            'name',
            'slug',
            'description',
            'logo_url',
            'last_links_checked_at',
        ]

        read_only_fields = fields