# Processor Service

Маленький обработчик изображений без собственной базы данных.
Название папки process-service сохранено; имя контейнера — processor-service.

RabbitMQConsumer получает image.process из exchange image.commands и очереди
image.process. ProcessService скачивает оригинал из MinIO, через Pillow создаёт
JPEG до 400×400 и сохраняет files/{file_id}/thumbnail.jpg.

FileClient через httpx вызывает PATCH /internal/v1/files/{id}/processing,
processed или failed. KafkaProducer отправляет file.processing_started,
file.processed и file.processing_failed в file.events.

## Запуск

Из родительской папки: `docker compose up -d --build`.

Для отдельного запуска скопируйте `.env.example` в `.env`, настройте адреса
File Service, RabbitMQ, Kafka и MinIO:

```shell
uv sync --frozen
uv run uvicorn app.main:app --host 0.0.0.0 --port 8002
```

APP_CONFIG__THUMBNAIL_SIZE задаёт размер стороны (по умолчанию 400).
У сервиса только GET /health и GET /metrics. Публичных ручек обработки нет.

## Доставка и ошибки

Prefetch равен 1. ACK отправляется после обработки и Kafka-публикации.
Сбой HTTP, S3 или Kafka вызывает requeue с паузой 2 секунды.
Повреждённое изображение переводится в FAILED и не ставится на повторную обработку.
Некорректный JSON/контракт команды отклоняется без requeue.

event_id детерминирован по command_id и типу события, поэтому повторная доставка
не дублирует аналитику. Если файл уже READY, превью повторно не создаётся.
Время обработки при таком восстановлении не выдумывается и может отсутствовать в событии.
Метрики отражают попытки процесса, а аналитика — уникальные события.

## Проверки

```shell
uv run pytest tests -q
```

Проверяются размер/формат превью, callbacks, повреждённые файлы, повторная доставка,
отклонение неправильных команд и requeue при отказе зависимостей.
Полный тест с реальными брокерами: см. корневой README.
