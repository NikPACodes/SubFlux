from django.db import models


class Status(models.TextChoices):
    """
    Статус подписки
    """
    ACTIVE = "active", "Active"
    PAUSED = "paused", "Paused"
    CANCELED = "canceled", "Canceled"
    TRIAL = "trial", "Trial"
    EXPIRED = "expired", "Expired"


class Source(models.TextChoices):
    """
    # Источник данных
    """
    # Ручной ввод
    MANUAL = "manual", "Manual"
    # Импорт из файла
    IMPORT = "import", "Import"
    # Интеграция
    INTEGRATION = "integration", "Integration"


class Platform(models.TextChoices):
    """
    Тип платформы
    """
    WEB = 'web', 'Web'
    IOS = 'ios', 'IOS'
    ANDROID = 'android', 'Android'
    DESKTOP = 'desktop', 'Desktop'
    TV = 'tv', 'TV'
    UNKNOWN = 'unknown', 'Unknown'


class LinkType(models.TextChoices):
    """
    Тип ссылки
    """
    # Управление оплатой/подпиской
    BILLING = 'billing', 'Billing'
    # Аккаунт/ЛК
    ACCOUNT = 'account', 'Account'
    # Поддержка
    SUPPORT = 'support', 'Support'
    # Тарифы/Цены
    PRICING = 'pricing', 'Pricing'


class PeriodUnit(models.TextChoices):
    """
    Единица периода
    """
    DAY = "day", "Day"
    WEEK = "week", "Week"
    MONTH = "month", "Month"
    YEAR = "year", "Year"