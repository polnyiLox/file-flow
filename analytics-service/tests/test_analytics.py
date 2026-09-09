from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from pymongo.errors import DuplicateKeyError

from app.broker.consumer import KafkaConsumer
from app.repositories.analytics import AnalyticsRepository
from app.schemas.event import EventMessage


def event():
    return EventMessage(
        event_id=uuid4(), event_type="file.processed",
        occurred_at=datetime.now(timezone.utc), producer="processor-service",
        payload={"file_id": str(uuid4()), "processing_time_ms": 200},
    )


@pytest.mark.asyncio
async def test_duplicate_event_is_ignored():
    collection = AsyncMock()
    collection.insert_one.side_effect = DuplicateKeyError("duplicate")
    repository = AnalyticsRepository({"analytics_events": collection})
    assert await repository.save_event(event()) is False


@pytest.mark.asyncio
async def test_event_date_is_stored_as_bson_datetime():
    collection = AsyncMock()
    repository = AnalyticsRepository({"analytics_events": collection})
    value = event()
    assert await repository.save_event(value) is True
    document = collection.insert_one.await_args.args[0]
    assert document["occurred_at"] == value.occurred_at
    assert document["event_id"] == str(value.event_id)


@pytest.mark.asyncio
async def test_empty_overview():
    collection = AsyncMock()
    cursor = AsyncMock()
    cursor.to_list.return_value = []
    collection.aggregate.return_value = cursor
    result = await AnalyticsRepository({"analytics_events": collection}).overview()
    assert result == {"files_uploaded": 0, "files_processed": 0, "files_failed": 0, "average_processing_ms": 0}


@pytest.mark.asyncio
async def test_consumer_saves_before_committing():
    repository = AsyncMock()
    order = []
    repository.save_event.side_effect = lambda value: order.append("save")
    message = SimpleNamespace(value=event().model_dump_json().encode(), partition=0, offset=0)
    broker = MagicMock()
    broker.__aiter__.return_value = [message]
    broker.commit = AsyncMock(side_effect=lambda: order.append("commit"))
    consumer = KafkaConsumer(None, repository)
    consumer._consumer = broker
    await consumer.consume()
    assert order == ["save", "commit"]


@pytest.mark.asyncio
async def test_invalid_event_does_not_reach_repository():
    repository = AsyncMock()
    consumer = KafkaConsumer(None, repository)
    await consumer.handle_message(SimpleNamespace(value=b"invalid", partition=0, offset=0))
    repository.save_event.assert_not_awaited()
