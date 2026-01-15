from django.db import models

from utils.validators import validator_region
from utils.enums import Platform, LinkType


class Provider(models.Model):
    """
    Provider - каталог сервисов/провайдеров подписок.

    Важно:
    - Все ссылки вынесены в ProviderLink т.к. имеют зависимость от платформ/регионов.
    - Provider хранит общие данные о сервисе.
    """

    name = models.CharField(max_length=128)
    slug = models.SlugField(max_length=128, unique=True, db_index=True)
    description = models.TextField(max_length=256)

    # URL логотипа/иконки сервиса, на начальных этапах ссылка проще, при необходимости переделается файл
    logo_url = models.URLField(blank=True, null=True)
    # Дата последней актуализации ссылок
    last_links_checked_at = models.DateTimeField(blank=True, null=True)

    is_active = models.BooleanField(default=True, db_index=True)
    create_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'providers'
        indexes = [
            #Индекс для ускорения поиска по именам активных сервисов
            models.Index(fields=["is_active", "name"]),
        ]

    def __str__(self):
        return self.name


class ProviderLink(models.Model):
    """
    ProviderLink - таблица ссылок сервисов по регионам и платформам

    Одному Provider может принадлежать несколько ссылок:
    - для разных стран/регионов (region)
    - для разных платформ (platform)
    - для разных типов ссылок (link_type)
    """

    provider = models.ForeignKey(Provider, on_delete=models.CASCADE, related_name="links")

    # Регион поле Char с соответствием формату:
    # ISO 3166-1 alpha-2 (US, DE, RU, ...) или GLOBAL
    region = models.CharField(max_length=8, default="GLOBAL", db_index=True, validators=[validator_region])

    platform = models.CharField(max_length=10, choices=Platform.choices, default=Platform.WEB, db_index=True)
    link_type = models.CharField(max_length=10, choices=LinkType.choices, db_index=True)
    url = models.URLField()

    # Дата последней проверки ссылки
    last_checked_at = models.DateTimeField(blank=True, null=True)
    is_active = models.BooleanField(default=True, db_index=True)
    create_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "provider_links"
        indexes = [
            # Индекс для ускорения поиска по региону/платформе/типу
            models.Index(fields=["provider", "region", "platform", "link_type"]),
        ]
        constraints = [
            # У каждого провайдера только один URL регион+платформа+тип
            models.UniqueConstraint(fields=["provider", "region", "platform", "link_type"],
                                    name="uniq_provider_region_platform_linktype"),
        ]

    def __str__(self):
        return f"{self.provider} [{self.region}/{self.platform}] {self.link_type}"