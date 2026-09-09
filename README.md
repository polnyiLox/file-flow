# File Service

Главный сервис FileFlow: принимает PNG/JPEG до 10 MiB, сохраняет оригинал в MinIO
и метаданные в PostgreSQL. После загрузки публикует image.process в RabbitMQ
и file.uploaded в Kafka. Удаление публикует file.deleted.

Структура обычная: router → FileService → FileRepository / клиенты инфраструктуры.
Одна SQLAlchemy-модель FileORM, миграции Alembic, Redis cache-aside на 300 секунд.

## Запуск

Рекомендуемый способ — `docker compose up -d --build` из родительской папки file-flow.
Все сервисы должны лежать рядом. Compose сам применяет миграции.

Для отдельного запуска подготовьте PostgreSQL, Redis, MinIO, RabbitMQ и Kafka,
скопируйте `.env.example` в `.env` и настройте адреса:

```shell
uv sync --frozen
uv run alembic upgrade head
uv run uvicorn app.main:app --host 0.0.0.0 --port 8001
```

Настройки читаются с префиксом APP_CONFIG__, вложенность разделяется __.
S3 ENDPOINT_URL нужен для связи сервиса с MinIO, PUBLIC_ENDPOINT_URL — для ссылок
в браузере. В Compose это http://minio:9000 и http://localhost:9000 соответственно.
Учётные данные в примере предназначены для локального учебного запуска.

## API

| Метод | Путь | Результат |
| --- | --- | --- |
| POST | /v1/files | multipart поле file, 201 и метаданные |
| GET | /v1/files | список, page и page_size (1–100) |
| GET | /v1/files/{id} | метаданные, 404 если нет |
| GET | /v1/files/{id}/download | original_url и thumbnail_url |
| DELETE | /v1/files/{id} | 204, во время обработки 409 |
| PATCH | /internal/v1/files/{id}/processing | PROCESSING |
| PATCH | /internal/v1/files/{id}/processed | READY, JSON с thumbnail_key |
| PATCH | /internal/v1/files/{id}/failed | FAILED |
| GET | /health | состояние HTTP-приложения |
| GET | /metrics | Prometheus |

Внешний доступ идёт через gateway с префиксом /api/v1/files.
Внутренние callbacks gateway не публикует. Статусы: UPLOADED, PROCESSING, READY, FAILED.
Проверка реального содержимого изображения выполняется обработчиком; повреждённый
PNG/JPEG получает FAILED. Ссылка на превью равна null до готовности.

S3-ключи: files/{id}/original.png (или jpg/jpeg), files/{id}/thumbnail.jpg.
При изменении статуса и удалении кэш инвалидируется после commit.
Повторный callback processing не сбрасывает READY.

## Проверки

```shell
uv run pytest tests/test_file_service.py tests/test_s3.py -q
uv run pytest tests/integration -q
```

Интеграционные тесты требуют Docker. Полный сценарий описан в корневом README.
Проект намеренно не использует outbox: при сбое публикации возможен UPLOADED без
команды. /health проверяет HTTP-процесс, а не доступность всех зависимостей.
