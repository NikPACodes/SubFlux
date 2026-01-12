"""
Domain services for Subscription

Бизнес-логика:
- запись/обновление цены + запись PriceHistory
- расчет next_run_at BillingSchedule
- синхронизация Subscription.next_billing_at
"""