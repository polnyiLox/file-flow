from .base import ExternalServiceError


class S3ServiceError(ExternalServiceError):
    detail = "S3 service is unavailable"