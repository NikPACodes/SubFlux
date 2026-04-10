from rest_framework import serializers
from apps.subscriptions.models import Category


class CategorySerializer(serializers.ModelSerializer):
    """
    Сериализатор для CRUD по справочнику категорий
    """
    class Meta:
        model = Category
        fields = [
            'id',
            'name',
            'slug',
            'icon',  # Идентификатор иконки для Frontend
            'sort_order',
            'create_at',
            'update_at',
        ]

        read_only_fields = [
            'id',
            'update_at',
            'create_at',
        ]


class CategoryPublicSerializer(serializers.ModelSerializer):
    """
    Публичный сериализатор для получения категорий
    """

    class Meta:
        model = Category
        fields = [
            'id',
            'name',
            'slug',
            'icon',  # Идентификатор иконки для Frontend
            'sort_order',
        ]

        read_only_fields = fields