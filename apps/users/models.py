from django.db import models
from django.contrib.auth.models import AbstractUser
from  phonenumber_field.modelfields import PhoneNumberField
from .managers import UserManager

# Create your models here.
class User(AbstractUser):
    """
    Кастомный пользователь SubFlux на базе AbstractUser.

    - username: ОБЯЗАТЕЛЬНЫЕ поля (уникальные):
      username, email
    - дополнительные поля (необязательные):
      phone, bio, gender, birth_date, first_name, last_name

    Аутентификация:
    - Django может иметь только один USERNAME_FIELD. Используем email как основной идентификатор.
    - Вход по username ИЛИ email делается через настройки allauth (ACCOUNT_LOGIN_METHODS).
    """
    username = models.CharField(max_length=150, unique=True, blank=False, null=False, db_index=True)
    email = models.EmailField(unique=True, blank=False, null=False, db_index=True)
    first_name = models.CharField(max_length=100, blank=True, null=True)
    last_name = models.CharField(max_length=100, blank=True, null=True)
    bio = models.TextField(max_length=300, blank=True, null=True)
    phone = PhoneNumberField(unique=True, blank=True, null=True)

    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
        ('U', 'Unspecified'),
    ]
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, default='U')
    birth_date = models.DateField(blank=True, null=True)
    update_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    objects = UserManager()

    def __str__(self):
        return self.username