# Start App Mongo

Переиспользуемый шаблон асинхронного приложения на FastAPI и MongoDB.

## Что уже настроено

- FastAPI и Uvicorn;
- асинхронный официальный драйвер `pymongo.AsyncMongoClient`;
- конфигурация через Pydantic Settings и `.env`;
- подключение и корректное закрытие MongoDB через lifespan FastAPI;
- проверка соединения с MongoDB при запуске приложения;
- CORS middleware;
- базовый обработчик ошибок;
- версионирование API через `/v1`;
- endpoint `GET /health`;
- слои `api`, `services`, `repositories`, `schemas` и `enums`;
- production и development Docker Compose;
- основа для интеграционных тестов с MongoDB Testcontainer;
- управление зависимостями через `uv`.

Motor намеренно не используется. Для новых асинхронных приложений MongoDB рекомендует Async API официального драйвера PyMongo.

## Требования

- Python 3.14;
- uv;
- Docker и Docker Compose для контейнерного запуска.

## Подготовка

Скопируй файл с примером настроек:

```powershell
Copy-Item .env.example .env
```

Установи зависимости:

```powershell
uv sync
```

Значения по умолчанию в `.env.example` предназначены для Docker Compose. Для запуска API напрямую на компьютере измени:

```env
APP_CONFIG__MONGODB__HOST=localhost
```

## Запуск для разработки

Полностью в Docker:

```powershell
docker compose -f docker-compose.dev.yaml up --build
```

Или MongoDB в Docker, а API локально:

```powershell
docker compose -f docker-compose.dev.yaml up mongodb
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

После запуска доступны:

- API: `http://localhost:8000`;
- Swagger UI: `http://localhost:8000/docs`;
- ReDoc: `http://localhost:8000/redoc`;
- health check: `http://localhost:8000/health`.

## Production-запуск

```powershell
docker compose up --build -d
```

Production-образ запускает приложение от непривилегированного пользователя и устанавливает только основные зависимости.

## Структура

```text
start_app_mongo/
├── app/
│   ├── api/
│   │   ├── dependencies.py
│   │   └── routers/
│   │       └── v1/
│   ├── core/
│   │   ├── config.py
│   │   └── health.py
│   ├── db/
│   │   └── mongodb.py
│   ├── enums/
│   ├── exceptions/
│   ├── repositories/
│   ├── schemas/
│   ├── services/
│   └── main.py
├── tests/
│   └── conftest.py
├── .env.example
├── Dockerfile
├── Dockerfile.dev
├── docker-compose.yaml
├── docker-compose.dev.yaml
├── pyproject.toml
└── uv.lock
```

## Как добавлять функционал

Рекомендуемый поток для новой сущности:

1. Pydantic-схемы разместить в `app/schemas`.
2. Запросы к MongoDB разместить в `app/repositories`.
3. Бизнес-логику разместить в `app/services`.
4. HTTP-ручки разместить в `app/api/routers/v1`.
5. Подключить новый router в `app/api/routers/v1/__init__.py`.

Базу можно получить через FastAPI dependency:

```python
from typing import Annotated

from fastapi import Depends
from pymongo.asynchronous.database import AsyncDatabase

from app.api.dependencies import get_database


Database = Annotated[AsyncDatabase, Depends(get_database)]
```

В репозитории коллекция выбирается так:

```python
class ExampleRepository:
    def __init__(self, database: AsyncDatabase) -> None:
        self.collection = database["examples"]
```

MongoDB не требует Alembic. Индексы и правила валидации коллекций следует создавать отдельно при появлении конкретных моделей проекта.

## Тесты

В шаблоне пока нет тестовых сценариев, но подготовлен `tests/conftest.py`. Он запускает временную MongoDB через Testcontainers и предоставляет fixture `database`:

```powershell
uv run pytest
```

Для интеграционных тестов должен быть запущен Docker.
