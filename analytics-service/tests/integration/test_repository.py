from datetime import datetime, timezone
from uuid import uuid4

import pytest

from app.repositories.analytics import AnalyticsRepository
from app.schemas.event import EventMessage


@pytest.mark.asyncio(loop_scope="session")
async def test_real_mongo_deduplication_and_aggregation(database):
    repository = AnalyticsRepository(database)
    await repository.create_indexes()
    file_id = str(uuid4())
    def event(kind, **payload):
        return EventMessage(
            event_id=uuid4(), event_type=kind, producer="test",
            occurred_at=datetime.now(timezone.utc),
            payload={"file_id": file_id, **payload},
        )
    upload = event("file.uploaded", size=100)
    assert await repository.save_event(upload)
    assert not await repository.save_event(upload)
    await repository.save_event(event("file.processed", processing_time_ms=200))
    await repository.save_event(event("file.processed", processing_time_ms=400))
    await repository.save_event(event("file.processing_failed"))
    assert await repository.overview() == {
        "files_uploaded": 1, "files_processed": 2, "files_failed": 1,
        "average_processing_ms": 300,
    }
    assert len(await repository.get_events(["file.uploaded"], 0, 10)) == 1
