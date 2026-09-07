import logging

from .config import settings


def configure_logging(level: str | None = None) -> None:
    logging.basicConfig(
        level=level or settings.logging.level,
        format=settings.logging.format,
        handlers=settings.logging.handlers,
        force=True
    )