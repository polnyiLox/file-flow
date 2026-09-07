from .base import ExternalServiceError


class RedisNotConnectedError(ExternalServiceError):
    detail = "Redis service is unavailable"