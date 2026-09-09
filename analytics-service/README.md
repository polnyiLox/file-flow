# Analytics Service

Kafka consumer слушает file.events и сохраняет события в MongoDB,
коллекция analytics_events. Router → AnalyticsService → AnalyticsRepository.

Уникальный индекс event_id делает обработку повторных сообщений идемпотентной.
Offset подтверждается вручную после insert. Если insert или commit не удался,
текущее сообщение повторяется. Некорректные события логируются и пропускаются.

## Запуск

Из родительской папки: `docker compose up -d --build`.

Для отдельного запуска скопируйте `.env.example` в `.env` и настройте MongoDB и Kafka:

```shell
uv sync --frozen
uv run uvicorn app.main:app --host 0.0.0.0 --port 8003
```

Настройки APP_CONFIG__MONGODB__*, APP_CONFIG__KAFKA__*.
По умолчанию группа Kafka analytics-service, auto_offset_reset=earliest.
Индексы создаются при запуске.

## API

| Путь | Ответ |
| --- | --- |
| GET /v1/analytics/overview | files_uploaded, files_processed, files_failed, average_processing_ms |
| GET /v1/analytics/uploads | список file.uploaded |
| GET /v1/analytics/processing | список started/processed/failed |
| GET /health | 503, если фоновый consumer завершился |
| GET /metrics | Prometheus |

Списки принимают page (от 1), page_size (1–100), сортируются от новых к старым.
Overview использует MongoDB aggregation. Среднее считается только по file.processed
с числовым processing_time_ms. При отсутствии данных возвращается 0.
Счётчики исторические: удаление файла не уменьшает число загрузок.

Внешний префикс gateway: /api/v1/analytics.
События сохраняются асинхронно; сразу после загрузки статистика может ещё не обновиться.

## Проверки

```shell
uv run pytest tests/test_analytics.py -q
uv run pytest tests/integration -q
```

Второй запуск требует Docker и проверяет настоящую MongoDB: индекс, дубликаты,
агрегацию. Сквозной тест описан в корневом README.
