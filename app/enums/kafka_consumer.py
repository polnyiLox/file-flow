from enum import StrEnum


class ProcessorEventTypes(StrEnum):
    PROCESSING_STARTED = "file.processing_started"
    PROCESSING_COMPLETED = "file.processed"
    PROCESSING_FAILED = "file.processing_failed"
