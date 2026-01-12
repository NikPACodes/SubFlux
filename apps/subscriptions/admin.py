from django.contrib import admin
from .models import Subscription, Provider, ProviderLink, Category, BillingSchedule, PriceHistory

# Register your models here.
@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    """
    Админка подписки
    """
    list_display = ('id', 'title', 'user', 'status',
                    'current_price_amount', 'current_price_currency', 'next_billing_at')
    readonly_fields = ('create_at', 'update_at')
    search_fields = ('title', 'user__email', 'user__username',)
    list_filter = ('status', 'provider', 'category',)
    autocomplete_fields = ('provider', 'category')

@admin.register(Provider)
class ProviderAdmin(admin.ModelAdmin):
    """
    Админка провайдеров (каталог сервисов)
    """
    list_display = ('id', 'name', 'slug', 'is_active', 'last_links_checked_at')
    readonly_fields = ('create_at', 'update_at')
    search_fields = ('name', 'slug',)
    list_filter = ('is_active',)

@admin.register(ProviderLink)
class ProviderLinkAdmin(admin.ModelAdmin):
    """
    Админка ссылок провайдера
    """
    list_display = ('provider', 'link_type', 'platform', 'region', 'is_active')
    readonly_fields = ('create_at', 'update_at')
    search_fields = ('provider__name', 'url',)
    list_filter = ('link_type', 'platform', 'region', 'is_active',)

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """
    Админка категорий
    """
    list_display = ('id', 'name', 'slug', 'sort_order')
    search_fields = ('name', 'slug',)

@admin.register(BillingSchedule)
class BillingScheduleAdmin(admin.ModelAdmin):
    """
    Админка расписания списаний
    """
    list_display = ('id', 'subscription', 'period_unit', 'period_interval', 'is_current', 'next_run_at')
    readonly_fields = ('create_at', 'update_at',)
    search_fields = ('subscription__title',)
    list_filter = ('period_unit', 'is_current',)

@admin.register(PriceHistory)
class PriceHistoryAdmin(admin.ModelAdmin):
    """
    Админка истории цен
    """
    list_display = ('id', 'subscription', 'amount', 'currency', 'effective_from', 'effective_to', 'source')
    readonly_fields = ('create_at',)
    search_fields = ('subscription__title',)
    list_filter = ('source', 'currency',)
