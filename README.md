# TG Family Bot

Личный Telegram-бот для обзоров и напоминалок.

## Структура проекта

```
tg_family/
├── tg_family/
│   ├── bot/          # Основной файл бота
│   ├── database/     # Модели и сессии БД
│   ├── handlers/     # Обработчики команд
│   ├── middlewares/  # Middleware (белый список)
│   ├── scheduler/    # Планировщик задач
│   └── alembic/      # Миграции БД
├── alembic.ini       # Конфигурация Alembic
├── pyproject.toml    # Зависимости (uv)
├── Dockerfile        # Docker образ
└── docker-compose.yml # Docker Compose
```

## Установка

### Локальная разработка

1. Установите зависимости:
```bash
cd tg_family
uv sync
```

2. Создайте файл `.env` на основе `.env.example`:
```bash
cp .env.example .env
```

3. Заполните `.env` (смотрите комментарии в файле)

4. Запустите миграции:
```bash
uv run alembic upgrade head
```

5. Запустите бота:
```bash
uv run python -m tg_family.bot.bot
```

### Docker

1. Создайте файл `.env` (см. выше)

2. Соберите и запустите:
```bash
cd tg_family
docker-compose up -d --build
```

## Команды управления

### Миграции базы данных

Создать новую миграцию:
```bash
uv run alembic revision --autogenerate -m "Описание"
```

Применить миграции:
```bash
uv run alembic upgrade head
```

Откатить миграцию:
```bash
uv run alembic downgrade -1
```

## Этапы реализации

1. ✅ Каркас: бот, белый список, база данных, планировщик
2. ⏳ Напоминания: дни рождения, дела, таблетки
3. ⏳ Настройки уведомлений (громко и тихо), удобное меню
4. ⏳ Команда /faq с описанием всех функций
5. ⏳ Автопостинг обзоров
6. ⏳ Интеграция с Google Calendar
