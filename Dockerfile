# ============================================================
# BUILDER
# ============================================================

FROM python:3.14-slim AS builder

WORKDIR /app

# Устанавливаем uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Сначала копируем только файлы зависимостей
COPY pyproject.toml uv.lock ./

# Устанавливаем production-зависимости
# непосредственно в системный Python.
RUN uv sync --frozen --no-dev --system

# Теперь копируем исходный код
COPY . .


# ============================================================
# RUNTIME
# ============================================================

FROM python:3.14-slim AS runtime

WORKDIR /app

# Переносим установленные Python-пакеты
# из builder в runtime.
COPY --from=builder /usr/local/lib/python3.13/site-packages \
                    /usr/local/lib/python3.13/site-packages

# Переносим исполняемые файлы,
# установленные вместе с пакетами.
COPY --from=builder /usr/local/bin \
                    /usr/local/bin

# Переносим приложение
COPY --from=builder /app/app /app/app

# Если используешь Alembic:
COPY --from=builder /app/alembic /app/alembic
COPY --from=builder /app/alembic.ini /app/alembic.ini

# Если приложение использует templates/static:
# COPY --from=builder /app/templates /app/templates
# COPY --from=builder /app/static /app/static

# Создаем непривилегированного пользователя
RUN useradd --create-home appuser

USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port","8000"]