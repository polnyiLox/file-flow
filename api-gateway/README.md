# API Gateway

Простой FastAPI proxy на httpx.AsyncClient.

На / расположен фронтенд FileFlow: загрузка PNG/JPEG, список файлов с превью,
статусы обработки, скачивание оригинала/превью и удаление с подтверждением.
Исходники — app/static/index.html, style.css и app.js. Никаких frontend-зависимостей
или отдельной сборки нет. API-запросы идут на тот же адрес, поэтому CORS не нужен.

- /api/v1/files → File Service /v1/files.
- /api/v1/files/{path} → файловые GET/DELETE.
- /api/v1/analytics/overview, uploads, processing → Analytics Service.
- /health — HTTP health, /metrics — Prometheus.

Внутренние callbacks и Processor Service наружу не выставляются.
Proxy сохраняет тело, query-параметры, статус и обычные заголовки.
Заголовки отдельного HTTP-соединения не пересылаются.
При недоступном сервисе возвращается 502, при таймауте — 504.
Максимальное тело запроса 11 MiB (с запасом для multipart), превышение — 413.

## Запуск

Из родительской папки: `docker compose up -d --build`.
Gateway доступен на http://localhost:8000.

Отдельно, после настройки адресов в `.env` по примеру `.env.example`:

```shell
uv sync --frozen
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
uv run pytest tests -q
```

APP_CONFIG__FILE_SERVICE_URL и APP_CONFIG__ANALYTICS_SERVICE_URL задают upstream.
APP_CONFIG__TIMEOUT_SECONDS — таймаут (30 секунд).
APP_CONFIG__MAX_BODY_SIZE — лимит в байтах (11534336).

Авторизации нет по ТЗ.
