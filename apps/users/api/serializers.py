from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.users.services import register_user

User = get_user_model()

class UserCreateSerializer(serializers.ModelSerializer):
    """
    Сериализатор создания пользователя

    password - не является обязательным (прим. OTP)
    """
    password = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'username',
            'password',
            'first_name',
            'last_name',
            'bio',
            'phone',
            'gender',
            'birth_date',
        ]
        read_only_fields = [
            'id',
            'update_at',
        ]

    def create(self, validated_data):
        return register_user(**validated_data)


class UserDetailSerializer(serializers.ModelSerializer):
    """
    Сериализатор для чтения и обновления пользователя админом

    Не имеет возможности редактировать password
    """
    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'bio',
            'phone',
            'gender',
            'birth_date',
            'is_active',
            'is_staff',
            'is_superuser',
            'last_login',
            'date_joined',
            'update_at',
        ]
        read_only_fields = [
            'id',
            'is_superuser',
            'last_login',
            'date_joined',
            'update_at',
        ]


class UserPublicSerializer(serializers.ModelSerializer):
    """
    Сериализатор публичного представления пользователя
    """
    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'first_name',
            # 'last_name',
        ]
        read_only_fields = fields