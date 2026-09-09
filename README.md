# FileFlow

Учебный проект для загрузки и асинхронной обработки PNG/JPEG изображений.

Gateway → File Service → RabbitMQ → Processor Service → HTTP callback.
Оригиналы и превью лежат в MinIO, метаданные — в PostgreSQL, кэш — в Redis.
File Service и Processor отправляют события в Kafka. Analytics сохраняет их в MongoDB.

## Запуск

Нужны Docker Desktop с Linux Engine и Docker Compose. Из этой папки:

```shell
docker compose up -d --build
docker compose ps
```

Compose применяет миграцию PostgreSQL, File Service создаёт бакет MinIO.
Файл `.env` для общего запуска не нужен: используются учебные настройки из Compose
и `file-service/.env.example`. Существующие локальные `.env` не изменяются.

| Адрес | Назначение | Учебный логин |
| --- | --- | --- |
| http://localhost:8000/docs | API Gateway | — |
| http://localhost:9001 | MinIO Console | minioadmin / minioadmin |
| http://localhost:15672 | RabbitMQ | file / file |
| http://localhost:9090 | Prometheus | — |
| http://localhost:3000 | Grafana, FileFlow Overview | admin / admin |

Внутренние API и базы не опубликованы на хост. Порты привязаны к localhost.
Это локальный учебный запуск без авторизации, не конфигурация для публичного сервера.

## Пример

В PowerShell используйте `curl.exe`, в Linux — `curl`.

```shell
curl.exe -F "file=@photo.png" http://localhost:8000/api/v1/files
curl.exe http://localhost:8000/api/v1/files/FILE_ID
curl.exe http://localhost:8000/api/v1/files/FILE_ID/download
curl.exe http://localhost:8000/api/v1/analytics/overview
curl.exe -X DELETE http://localhost:8000/api/v1/files/FILE_ID
```

Поддерживаются PNG/JPEG до 10 MiB. Статус меняется с UPLOADED на PROCESSING,
затем READY или FAILED. Превью — JPEG до 400×400 с сохранением пропорций.
`download` возвращает подписанные ссылки на оригинал и превью сроком на час.
До завершения обработки удаление возвращает 409.

## Сервисы

- [File Service](file-service/README.md): API, PostgreSQL, MinIO, Redis, RabbitMQ publisher.
- [Processor Service](process-service/README.md): RabbitMQ consumer, Pillow, HTTP callback, Kafka producer.
- [Analytics Service](analytics-service/README.md): Kafka consumer, MongoDB, три отчёта.
- [API Gateway](api-gateway/README.md): HTTP proxy на httpx.

Сервисы и общая инфраструктура находятся в одном репозитории. Истории исходных
репозиториев сохранены при объединении. Тест полного сценария находится в корневой папке. Имя папки обработчика
`process-service` сохранено; в Compose он называется `processor-service`.

## Разработка и тесты

```shell
docker compose -f docker-compose.yaml -f docker-compose.dev.yaml up -d --build
```

В режиме разработки исходники монтируются в контейнеры, Uvicorn перезапускается
при изменении файлов. Зависимости управляются через uv, Python 3.14.

В каждой папке сервиса:

```shell
uv sync --frozen
uv run pytest tests --ignore=tests/integration -q
```

Тест полного сценария требует запущенный общий стек. Из корня:

```shell
uv run --directory process-service python ../tests/e2e.py
```

Он загружает PNG, ждёт READY, скачивает оригинал и JPEG-превью, проверяет Kafka →
MongoDB через Analytics API, обрабатывает повреждённое изображение и удаляет
созданные файлы. Тест проверяет и повторное чтение метаданных через кэш.

Для интеграционных тестов PostgreSQL и MongoDB из папки соответствующего сервиса:

```shell
uv run pytest tests/integration -q
```

Они запускают временные контейнеры через testcontainers.

## Наблюдаемость

Все приложения отдают `/metrics`. Prometheus собирает HTTP-счётчики и длительности,
число загрузок, обработок, ошибок и Kafka-событий. Dashboard FileFlow Overview
автоматически появляется в Grafana. Alloy собирает Docker stdout в Loki.

Пример запроса в Grafana Explore с источником Loki:

```logql
{service="processor-service"} | json
```

Приложения пишут JSON-логи; file_id и command_id находятся в сообщениях обработчика.

## Остановка и ограничения

```shell
docker compose down
```

Именованные тома сохраняют данные. `docker compose down -v` удалит данные проекта.

RabbitMQ использует durable-очередь, persistent-сообщения, ACK и requeue при сбое
зависимостей. Повреждённое изображение получает FAILED, некорректная команда
отклоняется без requeue. Kafka offsets подтверждаются после сохранения в MongoDB;
уникальный event_id убирает дубликаты. Некорректные Kafka-сообщения логируются и
пропускаются, чтобы не останавливать партицию.

Outbox, DLQ, авторизации и распределённых транзакций здесь нет по ТЗ. При сбое
между записью файла и публикацией команды файл может остаться UPLOADED.
Неопределённый результат публикации требует проверки состояния файла; автоматической
гарантии доставки между PostgreSQL, S3 и брокерами нет. При восстановлении после
READY повторная обработка не запускается; если исходное событие не дошло, повторное
событие может не содержать время обработки. Среднее считается по имеющимся значениям.

Redis работает как необязательный кэш с TTL 300 секунд. При параллельном чтении
и изменении возможны устаревшие метаданные до истечения TTL.
Для доступа с другого компьютера потребуется отдельно настроить публикацию портов
и S3_PUBLIC_ENDPOINT_URL; подписанный URL нельзя менять после генерации.

