"""
Subscriptions app package.

Основное приложение, отвечающее за сущности подписок:
- Subscription (подписка пользователя)
- Provider/ProviderLink (каталог сервисов и ссылки)
- Category (категории)
- BillingSchedule (расписание списаний)
- PriceHistory (история цен)

Логику (расчёты next_run_at, обновление next_billing_at и т.п.) выносим в services/ и tasks/.
"""