from fastapi import status

from .base import AppError


class FileError(AppError):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    detail = "Error during working with file"


class ForbiddenFileExtensionError(FileError):
    status_code = status.HTTP_422_UNPROCESSABLE_CONTENT
    detail = "File extension not allowed"


class FilenameMissedError(FileError):
    status_code = status.HTTP_422_UNPROCESSABLE_CONTENT
    detail = "Filename missed"


class InvalidFilenameError(FileError):
    status_code = status.HTTP_422_UNPROCESSABLE_CONTENT
    detail = "Invalid filename"


class InvalidFileFormatError(FileError):
    status_code = status.HTTP_422_UNPROCESSABLE_CONTENT

    def __init__(self, message: str = "Invalid file format") -> None:
        self.detail = message


class FileORMNotFoundError(FileError):
    status_code = status.HTTP_404_NOT_FOUND
    detail = "File not found"