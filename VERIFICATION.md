# Проверки — 9 сентября 2026

- File Service: 10 unit-тестов прошли.
- Processor Service: 6 unit-тестов прошли.
- Analytics Service: 5 unit-тестов прошли.
- API Gateway: 6 unit-тестов прошли.
- Production и development Docker Compose: config --quiet прошёл.
- Alembic upgrade head --sql: миграция PostgreSQL успешно генерируется.
- Интеграционные тесты PostgreSQL и MongoDB успешно собираются (collect-only).

Docker Engine недоступен: отсутствует pipe dockerDesktopLinuxEngine.
Поэтому сборка контейнеров, интеграционные тесты и tests/e2e.py не выполнены.
После запуска Docker Desktop: docker compose up -d --build, затем команды тестов
из README.md. Эти проверки нельзя считать прошедшими до реального запуска.
