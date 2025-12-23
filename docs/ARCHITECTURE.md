# SubFlux — Архитектура и доменная модель

## 🧠 Архитектурный подход
__SubFlux — Django-проект с API-first подходом.__ 

- Основной интерфейс — __Django REST Framework (DRF)__ 
- Все клиенты (Web, Telegram, будущие Mobile) работают через единое API 
- Классический Django используется: 
  - для админки 
  - сервисных страниц 
  - возможного простого Web UI 

Бизнес-логика изолирована от фреймворков и живёт в services.py

---

## 🧩 Доменная модель
### Subscription 
Отвечает на вопрос __«на что подписан пользователь»__. 
- сервис 
- категория 
- пользователь 
- статус (trial, active, paused, cancelled, expired) 

### BillingSchedule
Отвечает на вопрос __«когда и как происходят списания»__.
- период (monthly / yearly / custom) 
- last_payment_date 
- next_payment_date
- 
📌 Subscription и BillingSchedule — разные ответственности. 
Связь: __1 Subscription → 1 BillingSchedule__

### PriceHistory 
Неизменяемая история изменения цен. 
- цена 
- валюта 
- причина изменения 
- дата 

Используется для: 
- аналитики 
- прогнозирования 
- отслеживания динамики цен 


### Состояния подписки

???

---

## 🔁 Основные workflow
### Добавление подписки
1. API получает запрос
2. Serializer валидирует данные
3. Service layer:
   - создаёт Subscription
   - создаёт BillingSchedule
   - рассчитывает next_payment_date
4. Создаётся запись PriceHistory
5. После commit:
   - планируются уведомления
   - обновляется аналитика

### Ежедневная обработка
1. Celery Beat запускает задачу
2. Проверяются BillingSchedule
3. Генерируются события напоминаний
4. Уведомления доставляются по каналам

---

## 🔔 Уведомления 
Уведомления строятся на событиях:
- PaymentReminderEvent 
- PriceChangeEvent 

Доставка осуществляется через каналы:
- Email 
- Telegram 
- Push (планируется) 

События отделены от транспорта доставки. 

---

## 📊 Аналитика и прогнозы
### Analytics 
Отвечает на вопрос __«что было»__: 
 
- расходы по категориям 
- месячные и годовые суммы 
- тренды 

Использует агрегаты и кеширование. 

### Forecasts 
Отвечает на вопрос __«что будет»__: 
- прогноз будущих списаний 
- сценарные оценки 

📌 Прогнозы — гипотеза, а не факт.

---

## Плановая структура Django-проекта
```
    subflux/
    ├── config/                      # Конфигурация проекта
    │   ├── settings/        
    │   │   ├── init.py
    │   │   ├── base.py
    │   │   ├── dev.py
    │   │   └── prod.py
    │   ├── urls.py
    │   ├── celery.py
    │   └── init.py
    ├── apps/
    │   ├── init.py
    │   ├── users/                  # Пользователь и профиль
    │   │   ├── migrations/
    │   │   ├── init.py
    │   │   ├── admin.py
    │   │   ├── services.py
    │   │   ├── models.py
    │   │   ├── api/
    │   │   │   ├── serializers.py
    │   │   │   ├── views.py           ???
    │   │   │   └── urls.py            ???
    │   │   └── urls.py
    │   ├── subscriptions/          # Основное приложение
    │   │   ├── migrations/
    │   │   ├── init.py
    │   │   ├── admin.py
    │   │   ├── tasks/             # Celery задачи
    │   │   ├── models/
    │   │   │   ├── init.py
    │   │   │   ├── subscription.py      # Subscription
    │   │   │   ├── category.py          # Category (или SubscriptionCategory)
    │   │   │   ├── provider.py          # Provider (Сервис)
    │   │   │   ├── billing_schedule.py  # BillingSchedule
    │   │   │   └── price_history.py     # PriceHistory    
    │   │   ├── services/
    │   │   │   ├── init.py
    │   │   │   ├── subscription_service.py
    │   │   │   └── billing_service.py
    │   │   ├── api/
    │   │   │   ├── serializers.py
    │   │   │   ├── views.py
    │   │   │   └── urls.py
    │   │   └── tasks/
    │   │       ├── init.py
    │   │       └── maintenance.py       # пересчёты next_payment_date/health tasks
    │   ├── analytics/             # Аналитика и отчеты
    │   │   ├── init.py
    │   │   ├── admin.py
    │   │   ├── migrations/
    │   │   ├── models/
    │   │   │   ├── init.py
    │   │   │   └── aggregates.py        # (опционально) materialized aggregates
    │   │   ├── services/
    │   │   │   ├── init.py
    │   │   │   ├── aggregations.py
    │   │   │   ├── reports.py
    │   │   │   └── forecasts.py
    │   │   ├── api/
    │   │   │   ├── serializers.py
    │   │   │   ├── views.py
    │   │   │   └── urls.py
    │   │   └── tasks/
    │   │       ├── init.py
    │   │       └── recompute.py         # пересчёт агрегатов/кеша 
    │   ├── notifications/         # Уведомления
    │   │   ├── init.py
    │   │   ├── admin.py
    │   │   ├── migrations/
    │   │   ├── templates/         # Шаблоны сообщений
    │   │   ├── models/
    │   │   │   ├── init.py
    │   │   │   ├── notification_event.py   # NotificationEvent
    │   │   │   ├── delivery_attempt.py     # DeliveryAttempt (лог доставок/ретраи)
    │   │   │   └── notification_settings.py# NotificationSettings (каналы/дни)
    │   │   ├── services/
    │   │   │   ├── init.py
    │   │   │   ├── dispatcher.py           # создаёт события/планирует отправку
    │   │   │   └── channels.py             # Email/Telegram senders
    │   │   ├── api/
    │   │   │   ├── serializers.py
    │   │   │   ├── views.py
    │   │   │   └── urls.py
    │   │   └── tasks/
    │   │       ├── init.py
    │   │       ├── scheduler.py            # daily: генерирует события
    │   │       └── sender.py               # отправка по каналам
    ├── utils/
    │   ├── init.py
    │   ├── enums.py                 # статусы/типы/периоды
    │   ├── date_calculator.py       # Логика работы с датами
    │   ├── price_calculator.py      # Конвертация валют и периодичностей
    │   └── validators.py            # Кастомные валидаторы
    ├── docs/                      # Документация
    │   └── diagrams/
    ├── templates/
    ├── docker/
    │   ├── docker-compose.yml
    │   └── Dockerfile
    ├── manage.py
    ├── requirements/
    │   ├── base.txt
    │   ├── dev.txt
    │   └── prod.txt
    ├── manage.py
    ├── .env
    └── README.md
```

---

## 🔐 Безопасность и надежность
### Безопасность:
- JWT authentication
- Хеширование паролей
- Валидация входных данных
- Защита от SQL-инъекций и XSS
- Возможность входа по одноразовому паролю
- 2FA
- OTP login
- Расширенный rate limiting

### Надежность:
- Транзакции для критических операций
- Резервное копирование базы данных
- Мониторинг ошибок через Sentry
- Логирование всех операций
- Graceful degradation при ошибках

---

## ⚙️ Особенности реализации
### 1. Работа с датами и периодами
- Автоматический расчет следующих платежей на основе периода подписки
- Конвертация разных периодов к месячному эквиваленту для аналитики
- Учет рабочих/выходных дней при отправке напоминаний

### 2. Фоновая обработка
- Celery задачи для асинхронных операций
- Redis как брокер сообщений и кэш
- Планировщик Celery Beat для регулярных задач
- Мониторинг очередей через Flower

### 3. Аналитика в реальном времени
- Агрегация данных через Django ORM
- Кэширование результатов аналитики
- Инкрементальное обновление статистики
- Поддержка различных валют

### 4. User-centric дизайн
- Индивидуальные настройки уведомлений для каждого пользователя
- Гибкая система категорий
- Персонализированные отчеты
- Поддержка темной/светлой темы

---

## 📊 Бизнес-логика

### Добавление подписки:
1. Валидация входных данных
2. Расчет даты следующего платежа
3. Сохранение в базу данных
4. Создание записи в истории цен
5. Запуск фоновых задач:
   - Обновление аналитики
   - Планирование напоминаний

### Ежедневная проверка:
1. Поиск подписок с ближайшими платежами (7, 3, 1 день)
2. Проверка настроек уведомлений пользователя
3. Создание задач для отправки напоминаний
4. Отправка email/push уведомлений
   
---

## 🎨 Интерфейс пользователя
### Основные экраны:
1. Дашборд - обзор всех подписок и статистика
2. Список подписок - таблица с фильтрами и сортировкой
3. Детали подписки - полная информация и история
4. Аналитика - графики и отчеты по расходам
5. Настройки - персонализация уведомлений и категорий

---

## 📱 Мобильная версия:
- Progressive Web App (PWA)
- Push-уведомления
- Оффлайн-доступ к данным
- Быстрый доступ к основным функциям

---

## 🔧 Основные функции API
### Управление подписками:
```
    GET    /api/subscriptions/                 # Список всех подписок
    POST   /api/subscriptions/                 # Добавление новой подписки
    GET    /api/subscriptions/{id}/            # Детали подписки
    PUT    /api/subscriptions/{id}/            # Обновление подписки
    DELETE /api/subscriptions/{id}/            # Удаление подписки
```

### Аналитика и отчеты:
```
    GET    /api/analytics/monthly-summary/     # Сводка на месяц
    GET    /api/analytics/category-breakdown/  # Расходы по категориям
    GET    /api/analytics/upcoming-payments/   # Ближайшие платежи
    GET    /api/analytics/price-history/{id}/  # История цен подписки
```

### Уведомления и настройки:
```
    GET    /api/notifications/settings/        # Настройки уведомлений
    PUT    /api/notifications/settings/        # Обновление настроек
    GET    /api/notifications/history/         # История уведомлений
```