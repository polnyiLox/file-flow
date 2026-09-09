from enum import StrEnum


class FileEventsContentTypesEnum(StrEnum):
    FILE_UPLOADED = "file.uploaded"
    FILE_UPLOADING_FAILED = "file.uploading.failed"

    FILE_PROCESSED = "file.processed"

    FILE_DOWNLOADED = "file.downloaded"
    FILE_DOWNLOADING_FAILED = "file.downloading.failed"

    FILE_STATUS_UPDATED = "file.status.updated"

    FILE_DELETED = "file.deleted"
    FILE_DELETING_FAILED = "file.deleting.failed"