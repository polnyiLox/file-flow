# Start App — Стартер FastAPI приложения

Готовый к использованию шаблон для разработки асинхронного REST API на **FastAPI** с интеграцией **PostgreSQL**, **SQLAlchemy** и **Alembic**.

## 🚀 Возможности

- ✅ **FastAPI** — современный веб-фреймворк для Python
- ✅ **SQLAlchemy 2.0** — с асинхронной поддержкой
- ✅ **AsyncPG** — быстрый асинхронный драйвер для PostgreSQL
- ✅ **Alembic** — управление миграциями БД
- ✅ **Docker & Docker Compose** — готово для контейнеризации
- ✅ **Модульная архитектура** — разделение на слои (API, Services, Repositories, Models)
- ✅ **Обработка ошибок** — централизованная система исключений
- ✅ **Settings** — конфигурация через Pydantic Settings

## 📋 Требования

- **Python** >= 3.14
- **PostgreSQL** >= 12
- **Docker & Docker Compose** (опционально)

## 🔧 Установка и настройка

### 1. Клонирование проекта

```bash
git clone <repository-url>
cd start_app
```

### 2. Установка зависимостей

Проект использует **uv** для управления зависимостями:

```bash
uv sync
```

Или, если используешь pip:

```bash
pip install -e .
```

### 3. Переменные окружения

Создай файл `.env` в корне проекта с необходимыми переменными:

```env
# Database
POSTGRES_USER=postgres
POSTGRES_PASSWORD=password
POSTGRES_DB=start_app
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# API
APP_CONFIG__API__HOST=0.0.0.0
APP_CONFIG__API__PORT=8000
APP_CONFIG__API__RELOAD=true
APP_CONFIG__API__V1_PREFIX=/api/v1

# Database URL (format для приложения)
APP_CONFIG__DB__USER=postgres
APP_CONFIG__DB__PASSWORD=password
APP_CONFIG__DB__HOST=localhost
APP_CONFIG__DB__PORT=5432
APP_CONFIG__DB__NAME=start_app

# Middleware
APP_CONFIG__MIDDLEWARE__ALLOW_ORIGINS=["localhost:3000"]
APP_CONFIG__MIDDLEWARE__ALLOW_METHODS=["*"]
APP_CONFIG__MIDDLEWARE__ALLOW_HEADERS=["*"]
APP_CONFIG__MIDDLEWARE__ALLOW_CREDENTIALS=true
```

## 🏃 Запуск приложения

### Локальный запуск

```bash
# Активируем virtual environment
source .venv/bin/activate  # Linux/macOS
# или
.venv\Scripts\Activate.ps1  # Windows PowerShell

# Запускаем приложение
uv run python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Запуск с Docker Compose

```bash
docker-compose up
```

Приложение будет доступно по адресу `http://localhost:8000`

## 📚 Структура проекта

```
start_app/
├── app/
│   ├── __init__.py
│   ├── main.py                 # Точка входа FastAPI приложения
│   ├── api/
│   │   ├── __init__.py
│   │   ├── dependencies.py     # Зависимости для маршрутов
│   │   └── routers/
│   │       └── v1/             # API версии 1
│   ├── core/
│   │   ├── __init__.py
│   │   └── config.py           # Конфигурация приложения
│   ├── db/
│   │   ├── __init__.py
│   │   ├── session.py          # Сессия БД и конфигурация
│   │   └── models/
│   │       └── base.py         # Базовый класс для моделей
│   ├── exceptions/
│   │   ├── __init__.py
│   │   └── base.py             # Базовые исключения приложения
│   ├── repositories/           # Слой доступа к данным (DAL)
│   │   └── __init__.py
│   ├── schemas/                # Pydantic модели (DTO)
│   │   └── __init__.py
│   └── services/               # Бизнес-логика
│       └── __init__.py
├── alembic/                    # Миграции БД
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
├── tests/                      # Тесты
├── alembic.ini                 # Конфигурация Alembic
├── docker-compose.yaml         # Docker Compose конфигурация
├── Dockerfile                  # Docker образ (multi-stage build)
├── pyproject.toml              # Зависимости и метаданные проекта
└── README.md                   # Этот файл
```

## 🗄️ Работа с базой данных

### Создание миграции

```bash
# Создаём новую миграцию
uv run alembic revision --autogenerate -m "Add users table"
```

### Применение миграций

```bash
# Применяем все миграции
uv run alembic upgrade head

# Откатываем последнюю миграцию
uv run alembic downgrade -1
```

### История миграций

```bash
uv run alembic history
```

## 🏗️ Архитектура слоёв

### 1. **API Layer** (`app/api/`)
Маршруты и обработка HTTP запросов. Здесь размещаются роутеры для каждой версии API.

```python
# app/api/routers/v1/items.py
from fastapi import APIRouter

router = APIRouter(prefix="/items", tags=["items"])

@router.get("/")
async def list_items():
    return {"items": []}
```

### 2. **Services Layer** (`app/services/`)
Бизнес-логика приложения. Сервисы работают с repositories и выполняют основные операции.

```python
# app/services/item_service.py
class ItemService:
    def __init__(self, repository: ItemRepository):
        self.repository = repository
    
    async def create_item(self, item_data):
        return await self.repository.create(item_data)
```

### 3. **Repository Layer** (`app/repositories/`)
Слой доступа к данным. Repositories инкапсулируют логику работы с БД.

```python
# app/repositories/item_repository.py
class ItemRepository:
    async def create(self, item_data):
        # Создание записи в БД
        pass
```

### 4. **Models Layer** (`app/db/models/`)
SQLAlchemy модели, представляющие таблицы БД.

```python
# app/db/models/item.py
from sqlalchemy import String, Column, Integer
from app.db.models.base import Base

class Item(Base):
    __tablename__ = "items"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
```

### 5. **Schemas Layer** (`app/schemas/`)
Pydantic модели для валидации и сериализации данных.

```python
# app/schemas/item.py
from pydantic import BaseModel

class ItemCreate(BaseModel):
    name: str

class ItemResponse(BaseModel):
    id: int
    name: str
```

## 🛠️ Обработка ошибок

Проект использует централизованную систему обработки ошибок:

```python
# app/exceptions/base.py
class AppError(Exception):
    def __init__(self, detail: str, status_code: int = 400):
        self.detail = detail
        self.status_code = status_code
```

Использование:

```python
from app.exceptions import AppError

@app.get("/items/{item_id}")
async def get_item(item_id: int):
    if not item:
        raise AppError("Item not found", status_code=404)
    return item
```

## ⚙️ Конфигурация

Приложение использует **Pydantic Settings** для управления конфигурацией:

```python
# app/core/config.py
class Settings(BaseSettings):
    db: DataBaseSettings
    api: ApiSettings
```

Переменные окружения перепоясываются на основе переменных среды, начинающихся с `APP_CONFIG__`.

## 🧪 Тестирование

Создавай тесты в папке `tests/`:

```bash
# Запуск тестов
uv run pytest tests/

# С покрытием
uv run pytest tests/ --cov=app
```

## 🐳 Docker

### Сборка образа

```bash
docker build -t start-app:latest .
```

### Запуск контейнера

```bash
docker run -p 8000:8000 --env-file .env start-app:latest
```

## 📖 Полезные команды

```bash
# Активация виртуального окружения
uv venv

# Установка зависимостей
uv sync

# Запуск приложения
uv run uvicorn app.main:app --reload

# Создание миграции
uv run alembic revision --autogenerate -m "message"

# Применение миграций
uv run alembic upgrade head

# Проверка кода (если установлены linters)
uv run ruff check app/

# Форматирование кода
uv run black app/
```

## 📝 Лучшие практики

1. **Разделение ответственности** — каждый слой отвечает за свою область
2. **Асинхронность** — используй `async/await` везде
3. **Валидация** — используй Pydantic schemas для валидации входных данных
4. **Миграции** — всегда создавай миграции для изменений в БД
5. **Окружение** — используй `.env` файлы для конфигурации
6. **Тесты** — пиши юнит и интеграционные тесты
7. **Исключения** — используй кастомные исключения для обработки ошибок

**Готово к разработке! Happy coding! 🚀**
