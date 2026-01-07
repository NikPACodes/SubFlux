from django.contrib.auth.base_user import BaseUserManager

class UserManager(BaseUserManager):
    """
    Менеджер для кастомного пользователя SubFlux.

    Зачем нужен:
    - гарантирует, что email обязателен и нормализуется (приводится к стандартному виду)
    - корректно хеширует пароль через set_password()
    - корректно создаёт суперпользователя (is_staff/is_superuser)

    Важный момент:
    - Django требует методы create_user/create_superuser для команд вроде createsuperuser
      и для корректной работы админки/инструментов.
    """

    use_in_migrations = True

    def _create_user(self, email: str, password: str | None = None, **extra_fields):
        if not email:
            raise ValueError("Email is required")

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)

        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()

        user.save(using=self._db)
        return user

    def create_user(self, email: str, password: str | None = None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if not extra_fields.get("is_staff"):
            raise ValueError("Superuser must have is_staff=True")
        if not extra_fields.get("is_superuser"):
            raise ValueError("Superuser must have is_superuser=True")

        return self._create_user(email, password, **extra_fields)