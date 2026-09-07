from fastapi import status


class AppError(Exception):
    """Base error of all app"""
    status_code: int = 500
    detail: str = "App error"


class ExternalServiceError(AppError):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    detail: str = "External service is unavailable"