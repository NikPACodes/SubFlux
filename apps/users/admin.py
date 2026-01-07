from django.contrib import admin

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import User

# Register your models here.
@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    # какие колонки показывать в списке пользователей
    list_display = ("id", "username", "email", "is_staff", "is_active", "last_login")
    list_filter = ("is_staff", "is_superuser", "is_active", "gender")

    # поиск по основным идентификаторам
    search_fields = ("username", "email", "phone")
    ordering = ("id",)

    # поля в форме просмотра/редактирования пользователя
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("Personal info", {"fields": ("first_name", "last_name", "email", "phone", "bio", "gender", "birth_date")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login", "update_at", "date_joined")}),
    )

    # поля в форме создания пользователя в админке
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("username", "email", "password1", "password2", "is_staff", "is_active"),
        }),
    )