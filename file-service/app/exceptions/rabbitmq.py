from .base import ExternalServiceError


class RabbitMQServiceError(ExternalServiceError):
    detail = "RabbitMQ Service is unavailable"