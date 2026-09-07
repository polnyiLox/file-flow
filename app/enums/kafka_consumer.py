from enum import StrEnum


class ProcessorEventTypes(StrEnum):
    PROCESSING_STARTED = "file.processin_started"
    PROCESSING_COMPLETED = "file.processed"
    PROCESSING_FAILED = "file.processing_failed"