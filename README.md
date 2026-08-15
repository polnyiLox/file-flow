# Start App — Стартер FastAPI приложения

Готовый к использованию шаблон для разработки асинхронного REST API на **FastAPI** с интеграцией **PostgreSQL**, **SQLAlchemy** и **Alembic**. Проект включает все необходимое для быстрого старта разработки масштабируемых веб-приложений.

## 🚀 Возможности

- ✅ **FastAPI** — современный веб-фреймворк для Python с автоматической документацией (Swagger UI)
- ✅ **SQLAlchemy 2.0** — полнофункциональный ORM с асинхронной поддержкой
- ✅ **AsyncPG** — быстрый асинхронный драйвер для PostgreSQL
- ✅ **Alembic** — управление миграциями БД с версионированием
- ✅ **Docker & Docker Compose** — готово для контейнеризации и desarrollo среды
- ✅ **Модульная архитектура** — разделение на слои (API, Services, Repositories, Models)
- ✅ **Обработка ошибок** — централизованная система исключений
- ✅ **Settings** — конфигурация через Pydantic Settings с поддержкой .env файлов
- ✅ **CORS Middleware** — встроенная поддержка кросс-доменных запросов
- ✅ **Health Check** — встроенный endpoint для проверки состояния приложения

## 📋 Требования

- **Python** >= 3.14
- **PostgreSQL** >= 12
- **Docker & Docker Compose** (опционально, но рекомендуется)
- **uv** — быстрый менеджер пакетов для Python (опционально, но рекомендуется)

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

#### 1. Подготовка окружения

```bash
# Активируем virtual environment
source .venv/bin/activate  # Linux/macOS
# или
.venv\Scripts\Activate.ps1  # Windows PowerShell

# Убедимся, что зависимости установлены
uv sync
```

#### 2. Запуск локально (требует PostgreSQL)

```bash
# Запускаем приложение с автоперезагрузкой
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### 3. Запуск с Docker Compose (рекомендуется)

```bash
docker-compose up
```

Приложение будет доступно по адресу:
- **API**: `http://localhost:8000`
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### Встроенные endpoints

- `GET /health` — проверка состояния приложения

```bash
curl http://localhost:8000/health
# Ответ: {"status": "ok"}
```

## 📚 Структура проекта

```
start_app/
├── alembic/                    # Миграции БД (версионирование схемы)
│   ├── env.py                  # Конфигурация для миграций
│   ├── script.py.mako          # Шаблон для новых миграций
│   └── versions/               # Директория с файлами миграций
│
├── app/                        # Основное приложение
│   ├── __init__.py
│   ├── main.py                 # Точка входа FastAPI приложения
│   │
│   ├── api/                    # API маршруты и контроллеры
│   │   ├── __init__.py
│   │   ├── dependecies.py      # Зависимости (dependency injection)
│   │   └── routers/
│   │       ├── __init__.py
│   │       └── v1/             # API версии 1
│   │           └── __init__.py
│   │
│   ├── core/                   # Ядро приложения (конфиг, утилиты)
│   │   ├── __init__.py
│   │   ├── config.py           # Конфигурация (Settings)
│   │   └── health.py           # Health check router
│   │
│   ├── db/                     # Работа с базой данных
│   │   ├── __init__.py
│   │   ├── session.py          # Сессия БД, engine, SessionLocal
│   │   └── models/             # SQLAlchemy модели
│   │       ├── __init__.py
│   │       └── base.py         # Базовый класс для всех моделей
│   │
│   ├── exceptions/             # Кастомные исключения
│   │   ├── __init__.py
│   │   └── base.py             # AppError — базовый класс
│   │
│   ├── repositories/           # Слой доступа к данным (DAL)
│   │   └── __init__.py
│   │
│   ├── schemas/                # Pydantic модели (DTO, валидация)
│   │   └── __init__.py
│   │
│   └── services/               # Бизнес-логика приложения
│       └── __init__.py
│
├── tests/                      # Тесты
│   └── conftest.py             # Pytest конфигурация и fixtures
│
├── Dockerfile                  # Docker образ (multi-stage build)
├── Dockerfile.dev              # Dockerfile для разработки
├── docker-compose.yaml         # Production Docker Compose
├── docker-compose.dev.yaml     # Development Docker Compose
├── alembic.ini                 # Конфигурация Alembic
├── pyproject.toml              # Зависимости, метаданные проекта (uv)
└── README.md                   # Этот файл
```

## 🗄️ Работа с базой данных

### Создание миграции

```bash
# Создаём новую миграцию с автоматической генерацией SQL
uv run alembic revision --autogenerate -m "Add users table"

# Или создаём пустую миграцию для ручного заполнения
uv run alembic revision -m "Manual migration"
```

### Применение миграций

```bash
# Применяем все миграции до головы
uv run alembic upgrade head

# Откатываем последнюю миграцию
uv run alembic downgrade -1

# Откатываем до конкретной версии
uv run alembic downgrade <revision>
```

### История миграций

```bash
# Показывает историю всех миграций
uv run alembic history

# Показывает текущую версию
uv run alembic current
```

### Пример создания модели

```python
# app/db/models/user.py
from sqlalchemy import String, Column, Integer, DateTime
from sqlalchemy.sql import func
from app.db.models.base import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
```

## 🏗️ Архитектура слоёв

Приложение следует многоуровневой архитектуре для разделения ответственности:

### 1. **API Layer** (`app/api/`)
Обработка HTTP запросов, валидация, маршрутизация.

```python
# app/api/routers/v1/users.py
from fastapi import APIRouter, Depends
from app.schemas.user import UserCreate, UserResponse
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["Users"])

@router.post("/", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    service: UserService = Depends(get_user_service)
):
    return await service.create_user(user_data)

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    service: UserService = Depends(get_user_service)
):
    return await service.get_user(user_id)
```

### 2. **Services Layer** (`app/services/`)
Бизнес-логика приложения, обработка данных перед сохранением в БД.

```python
# app/services/user_service.py
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate
from app.exceptions import AppError

class UserService:
    def __init__(self, repository: UserRepository):
        self.repository = repository
    
    async def create_user(self, user_data: UserCreate):
        # Проверка уникальности email
        existing = await self.repository.get_by_email(user_data.email)
        if existing:
            raise AppError("Email уже зарегистрирован", status_code=400)
        
        # Создание пользователя
        return await self.repository.create(user_data)
    
    async def get_user(self, user_id: int):
        user = await self.repository.get_by_id(user_id)
        if not user:
            raise AppError("Пользователь не найден", status_code=404)
        return user
```

### 3. **Repository Layer** (`app/repositories/`)
Инкапсуляция логики работы с БД, CRUD операции.

```python
# app/repositories/user_repository.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models.user import User
from app.schemas.user import UserCreate

class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, user_data: UserCreate) -> User:
        user = User(**user_data.dict())
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user
    
    async def get_by_id(self, user_id: int) -> User | None:
        return await self.session.get(User, user_id)
    
    async def get_by_email(self, email: str) -> User | None:
        result = await self.session.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()
```

### 4. **Models Layer** (`app/db/models/`)
SQLAlchemy модели, представляющие таблицы БД.

```python
# app/db/models/base.py
from sqlalchemy.orm import declarative_base

Base = declarative_base()
```

### 5. **Schemas Layer** (`app/schemas/`)
Pydantic модели для валидации и сериализации данных.

```python
# app/schemas/user.py
from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    email: EmailStr
    name: str

class UserResponse(BaseModel):
    id: int
    email: str
    name: str
    
    class Config:
        from_attributes = True
```

## ⚙️ Конфигурация

Приложение использует **Pydantic Settings** для управления конфигурацией через переменные окружения.

### Структура конфигурации

```python
# app/core/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    db: DataBaseSettings        # Настройки БД
    api: ApiSettings           # Настройки API
    middleware: MIddlewareSettings  # Настройки middleware

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="APP_CONFIG__",
        env_nested_delimiter="__",  # Для вложенных переменных
        case_sensitive=False
    )
```

### Использование конфигурации

```python
from app.core.config import get_settings

settings = get_settings()
print(settings.db.url)      # postgresql+asyncpg://user:pass@host:5432/db
print(settings.api.v1_prefix)  # /api/v1
```

## 🛠️ Обработка ошибок

Проект использует централизованную систему обработки ошибок через кастомное исключение `AppError`:

```python
# app/exceptions/base.py
class AppError(Exception):
    """Базовое исключение приложения"""
    status_code: int = 500
    detail: str = "App error"
```

### Регистрация обработчика исключений

В `app/main.py` уже зарегистрирован обработчик для `AppError`:

```python
@app.exception_handler(AppError)
async def app_errors_handler(request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )
```

### Использование в приложении

```python
from app.exceptions import AppError

# Пример в сервисе
if not user:
    raise AppError("Пользователь не найден", status_code=404)

# Пример в API роутере
@router.get("/{user_id}")
async def get_user(user_id: int, service: UserService = Depends()):
    user = await service.get_user(user_id)
    return user
```

## 🧪 Тестирование

Проект поддерживает тестирование с помощью **pytest** и **pytest-asyncio**:

```bash
# Запуск всех тестов
uv run pytest tests/

# Запуск тестов с выводом покрытия
uv run pytest tests/ --cov=app

# Запуск конкретного файла тестов
uv run pytest tests/test_users.py

# Запуск с выводом подробностей
uv run pytest tests/ -v
```

### Пример теста

```python
# tests/test_users.py
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_get_health():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
```

### Конфигурация pytest

```python
# tests/conftest.py
# Здесь должны быть fixtures для БД, клиентов и т.д.
```

## 🐳 Docker

### Структура Dockerfile

Проект использует **multi-stage build** для оптимизации размера образа:

1. **Builder stage** — установка зависимостей с `uv`
2. **Runtime stage** — только необходимые файлы для запуска

### Сборка образа

```bash
# Сборка production образа
docker build -t start-app:latest .

# Сборка development образа
docker build -f Dockerfile.dev -t start-app:dev .
```

### Запуск контейнера

```bash
# С файлом переменных окружения
docker run -p 8000:8000 --env-file .env start-app:latest

# С явными переменными
docker run -p 8000:8000 \
  -e APP_CONFIG__DB__USER=postgres \
  -e APP_CONFIG__DB__PASSWORD=password \
  start-app:latest
```

### Docker Compose (рекомендуется)

```bash
# Запуск в режиме development
docker-compose -f docker-compose.dev.yaml up

# Запуск в режиме production
docker-compose up

# Остановка контейнеров
docker-compose down

# Просмотр логов
docker-compose logs -f app
```

## 📖 Полезные команды

### Управление виртуальным окружением

```bash
# Создание виртуального окружения
uv venv

# Активация (Linux/macOS)
source .venv/bin/activate

# Активация (Windows PowerShell)
.venv\Scripts\Activate.ps1
```

### Управление зависимостями

```bash
# Установка всех зависимостей
uv sync

# Добавление новой зависимости
uv add пакет_название

# Добавление dev-зависимости
uv add --dev пакет_название

# Обновление зависимостей
uv sync --upgrade
```

### Запуск приложения

```bash
# Локальный запуск с автоперезагрузкой
uv run uvicorn app.main:app --reload

# Запуск на определённом хосте и порте
uv run uvicorn app.main:app --host 0.0.0.0 --port 8080

# Запуск с несколькими рабочими процессами
uv run uvicorn app.main:app --workers 4
```

### Работа с базой данных

```bash
# Создание новой миграции
uv run alembic revision --autogenerate -m "описание"

# Применение всех миграций
uv run alembic upgrade head

# Откат на одну версию назад
uv run alembic downgrade -1

# Просмотр текущей версии
uv run alembic current
```

### Тестирование и качество кода

```bash
# Запуск тестов
uv run pytest tests/ -v

# С покрытием
uv run pytest tests/ --cov=app --cov-report=html

# Проверка синтаксиса (если установлен ruff)
uv run ruff check app/

# Форматирование кода (если установлен black)
uv run black app/
```

### Другие команды

```bash
# Показать версию Python
python --version

# Показать используемое окружение
which python  # Linux/macOS
where python  # Windows

# Установка расширений VS Code для Python
code --install-extension ms-python.python
code --install-extension ms-python.vscode-pylance
```

## 📝 Лучшие практики

### Архитектура и код

1. **Разделение ответственности** — каждый слой отвечает за свою область:
   - `API` — обработка HTTP запросов
   - `Services` — бизнес-логика
   - `Repositories` — работа с БД
   - `Models` — схема БД

2. **Асинхронность** — используй `async/await` везде для лучшей производительности

3. **Валидация данных** — всегда используй Pydantic schemas для входных и выходных данных

4. **Обработка ошибок** — используй кастомные исключения и централизованные обработчики

5. **Конфигурация** — используй `.env` файлы и Pydantic Settings для управления параметрами

### БД и миграции

6. **Миграции** — создавай миграции для всех изменений в схеме БД

7. **Типы данных** — используй правильные типы SQLAlchemy для колонок

8. **Индексы и ограничения** — добавляй индексы на часто запрашиваемые колонки

### Тестирование и документация

9. **Тесты** — пиши юнит и интеграционные тесты для критичного функционала

10. **Документация** — используй docstrings для документирования функций и классов

11. **Типизация** — используй type hints для улучшения читаемости и IDE поддержки

### Безопасность

12. **Переменные окружения** — никогда не коммиться `.env` файлы

13. **Валидация входных данных** — всегда валидируй входные данные через Pydantic

14. **CORS** — правильно конфигурируй CORS для фронтенд приложений

## 🤝 Контрибьютинг

Если ты нашёл ошибку или хочешь добавить функцию:

1. Создай новую ветку: `git checkout -b feature/my-feature`
2. Сделай изменения и напиши тесты
3. Убедись, что все тесты проходят: `uv run pytest`
4. Создай Pull Request

## 📄 Лицензия

Этот проект распространяется под MIT лицензией.

---

**Готово к разработке! Happy coding! 🚀**
