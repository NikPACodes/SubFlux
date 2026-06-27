from django.contrib import admin
from .models import (Subscription,
                     Provider, ProviderLink,
                     Category, BillingSchedule,
                     PriceHistory, VerifiedPrice,
                     Payment)

# Register your models here.
@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    """
    Админка подписки
    """
    list_display = ('id', 'title', 'user', 'provider', 'category', 'status',
                    'current_price_amount', 'current_price_currency', 'next_billing_at',
                    'is_shared', 'is_deleted')
    readonly_fields = ('status', 'started_at', 'ended_at',
                       'current_price_amount', 'current_price_currency',
                       'next_billing_at', 'last_billed_at', 'billing_timezone',
                       'create_at', 'update_at')

    search_fields = ('title', 'user__email', 'user__username', 'provider__name', 'category__name')
    list_filter = ('status', 'provider', 'category', 'is_shared', 'is_deleted', 'billing_timezone')

    autocomplete_fields = ('user', 'provider', 'category')
    list_select_related = ('user', 'provider', 'category')

    date_hierarchy = 'create_at'
    ordering = ('-create_at',)

    fieldsets = (
        ('Основное', {'fields': ('user', 'title', 'description', 'provider', 'category', 'status')},),
        ('Пользовательские настройки', {'fields': ('payment_method_label', 'owner_note', 'is_shared',
                                                   'billing_timezone', 'meta', 'is_deleted')},),
        ('Расчетные поля', {'fields': ('current_price_amount', 'current_price_currency',
                                       'next_billing_at', 'last_billed_at')},),
        ('Даты жизненного цикла', {'fields': ('started_at', 'ended_at', 'create_at', 'update_at')},),
    )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Provider)
class ProviderAdmin(admin.ModelAdmin):
    """
    Админка провайдеров (каталог сервисов)
    """
    list_display = ('id', 'name', 'slug', 'is_active', 'last_links_checked_at', 'create_at', 'update_at')
    readonly_fields = ('last_links_checked_at', 'create_at', 'update_at')

    search_fields = ('name', 'slug',)
    list_filter = ('is_active',)

    date_hierarchy = 'create_at'
    ordering = ('name',)


@admin.register(ProviderLink)
class ProviderLinkAdmin(admin.ModelAdmin):
    """
    Админка ссылок провайдера
    """
    list_display = ('id', 'provider', 'link_type', 'platform', 'region', 'is_active', 'last_checked_at')
    readonly_fields = ('last_checked_at', 'create_at', 'update_at')

    search_fields = ('provider__name', 'url',)
    list_filter = ('link_type', 'platform', 'region', 'is_active')

    autocomplete_fields = ('provider',)
    list_select_related = ('provider',)

    date_hierarchy = 'create_at'
    ordering = ('provider__name', 'region', 'platform', 'link_type')


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """
    Админка категорий
    """
    list_display = ('id', 'name', 'slug', 'icon', 'sort_order', 'create_at', 'update_at')
    readonly_fields = ('create_at', 'update_at')

    search_fields = ('name', 'slug',)

    date_hierarchy = 'create_at'
    ordering = ('sort_order', 'name')


@admin.register(BillingSchedule)
class BillingScheduleAdmin(admin.ModelAdmin):
    """
    Админка расписания списаний
    """
    list_display = ('id', 'subscription', 'period_unit', 'period_interval',
                    'anchor_day', 'anchor_weekday', 'trial_ends_at', 'next_run_at',
                    'is_current')
    readonly_fields = ('id', 'subscription', 'period_unit', 'period_interval',
                       'anchor_day', 'anchor_weekday', 'trial_ends_at', 'next_run_at',
                       'grace_days', 'is_current', 'create_at', 'update_at')

    search_fields = ('subscription__title', 'subscription__user__email', 'subscription__user__username')
    list_filter = ('period_unit', 'period_interval', 'is_current',)

    autocomplete_fields = ('subscription',)
    list_select_related = ('subscription', 'subscription__user')

    date_hierarchy = 'next_run_at'
    ordering = ('-is_current', 'next_run_at')


    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(PriceHistory)
class PriceHistoryAdmin(admin.ModelAdmin):
    """
    Админка истории цен
    """
    list_display = ('id', 'subscription', 'verified_price', 'amount', 'currency',
                    'effective_from', 'effective_to', 'source', 'create_at')
    readonly_fields = ('subscription', 'verified_price', 'amount', 'currency',
                    'effective_from', 'effective_to', 'change_reason', 'source', 'create_at')

    search_fields = ('subscription__title', 'subscription__user__email', 'subscription__user__username',
                     'verified_price__provider__name', 'verified_price__plan_name')
    list_filter = ('source', 'currency', 'effective_from', 'effective_to',)

    autocomplete_fields = ('subscription', 'verified_price')
    list_select_related = ('subscription', 'subscription__user', 'verified_price', 'verified_price__provider')

    date_hierarchy = 'effective_from'
    ordering = ('-effective_from',)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(VerifiedPrice)
class VerifiedPriceAdmin(admin.ModelAdmin):
    """
    Админка доверенных цен по тарифам провайдера.
    """
    list_display = ('id', 'provider', 'plan_name', 'region', 'amount', 'currency',
                    'period_unit', 'period_interval', 'platform', 'source', 'source_link',
                    'valid_from', 'valid_to', 'is_active')
    readonly_fields = ('update_at', 'create_at')

    search_fields = ('provider__name', 'provider__slug', 'plan_name', 'region')
    list_filter = ('region', 'platform', 'source', 'currency', 'period_unit', 'period_interval',
                   'valid_from', 'valid_to', 'is_active')

    autocomplete_fields = ('provider', 'source_link')
    list_select_related = ('provider', 'source_link')

    date_hierarchy = 'valid_from'
    ordering = ('provider__name', 'plan_name', 'region', 'platform')


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    """
    Админка факта списания.
    """
    list_display = ('id', 'subscription', 'amount', 'currency', 'paid_at', 'source', 'price_history', 'note',
                    'created_at')
    readonly_fields = ('subscription', 'amount', 'currency', 'paid_at', 'source', 'price_history', 'created_at')

    search_fields = ('subscription__title', 'subscription__user__email', 'subscription__user__username')
    list_filter = ('source', 'currency', 'paid_at')

    autocomplete_fields = ('subscription', 'price_history')
    list_select_related = ('subscription', 'subscription__user', 'price_history')

    date_hierarchy = 'paid_at'
    ordering = ('-paid_at', '-created_at')

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False