from django.db import models


class SubscriptionStatus(models.TextChoices):
    """
    Статус подписки
    """
    ACTIVE = "active", "Active"
    PAUSED = "paused", "Paused"
    CANCELED = "canceled", "Canceled"
    TRIAL = "trial", "Trial"
    DELAYED = "delayed", "Delayed"
    EXPIRED = "expired", "Expired"

class VerifiedPriceSource(models.TextChoices):
    """
    Источник данных (Подтвержденные цены)
    """
    ADMIN = "admin", "Admin"
    API = "api", "API"
    # Интеграция
    SYNC = "sync", "Sync"

class PriceHistorySource(models.TextChoices):
    """
    Источник данных (Цена)
    """
    # Подтвержденные цены (VerifiedPrice)
    VERIFIED = "verified", "Verified"
    # Ручной ввод
    MANUAL = "manual", "Manual"


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


class PaymentSource(models.TextChoices):
    """
    Источник данных (факт списания)
    """
    # Ручной ввод
    MANUAL = "manual", "Manual"
    # Импорт из файла
    IMPORT = "import", "Import"
    # Синхронизация
    SYNC = "sync", "Sync"


class WorkspaceType(models.TextChoices):
    """
    Тип рабочей области
    """
    PERSONAL = "personal", "Personal"
    TEAM = "team", "Team"
    ORGANIZATION = "organization", "Organization"


class WorkspaceStatus(models.TextChoices):
    """
    Состояние рабочей области
    """
    ACTIVE = "active", "Active"
    DEACTIVATED = "deactivated", "Deactivated"
    BLOCKED = "blocked", "Blocked"
    ARCHIVED = "archived", "Archived"
    DELETED = "deleted", "Deleted"