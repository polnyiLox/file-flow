from io import BytesIO
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from PIL import Image

from app.services.process import ProcessService
from app.broker.rabbitmq import RabbitMQConsumer
from app.schemas.rabbitmq_consumer import ProcessCommandEvent


def image_bytes():
    output = BytesIO()
    Image.new("RGBA", (800, 200), (255, 0, 0, 128)).save(output, "PNG")
    return output.getvalue()


def test_thumbnail_keeps_aspect_ratio_and_uses_jpeg():
    result = ProcessService(None, None, None).create_thumbnail(image_bytes())
    with Image.open(BytesIO(result)) as thumbnail:
        assert thumbnail.size == (400, 100)
        assert thumbnail.format == "JPEG"
        assert thumbnail.mode == "RGB"


@pytest.mark.asyncio
async def test_processing_updates_file_and_publishes_event():
    s3, files, kafka = AsyncMock(), AsyncMock(), AsyncMock()
    command = ProcessCommandEvent(command_id=uuid4(), command_type="image.process", file_id=uuid4(), original_key="original.png")
    files.get_file.return_value = {"status": "UPLOADED", "original_key": "original.png"}
    async def download(key):
        yield image_bytes()
    s3.download_file = download
    await ProcessService(s3, files, kafka).process_image(command)
    assert files.update_status.await_args_list[-1].args == (str(command.file_id), "processed")
    assert kafka.publish_event.await_args_list[-1].args[1] == "file.processed"
    assert s3.upload_file.await_args.args[1] == f"files/{command.file_id}/thumbnail.jpg"


@pytest.mark.asyncio
async def test_invalid_image_marks_failed():
    s3, files, kafka = AsyncMock(), AsyncMock(), AsyncMock()
    files.get_file.return_value = {"status": "UPLOADED", "original_key": "broken.png"}
    async def download(key):
        yield b"not an image"
    s3.download_file = download
    command = SimpleNamespace(file_id=uuid4(), command_id=uuid4(), original_key="broken.png")
    await ProcessService(s3, files, kafka).process_image(command)
    files.update_status.assert_any_await(str(command.file_id), "failed")
    assert kafka.publish_event.await_args.args[1] == "file.processing_failed"
    s3.upload_file.assert_not_awaited()


@pytest.mark.asyncio
async def test_ready_redelivery_does_not_reprocess():
    s3, files, kafka = AsyncMock(), AsyncMock(), AsyncMock()
    files.get_file.return_value = {"status": "READY", "original_key": "image.png"}
    command = SimpleNamespace(file_id=uuid4(), command_id=uuid4(), original_key="image.png")
    await ProcessService(s3, files, kafka).process_image(command)
    s3.download_file.assert_not_called()
    files.update_status.assert_not_awaited()
    assert kafka.publish_event.await_args.args[1] == "file.processed"


@pytest.mark.asyncio
async def test_invalid_command_is_rejected():
    message = AsyncMock()
    message.body = b'{"unexpected": true}'
    consumer = RabbitMQConsumer(None, AsyncMock())
    await consumer.handle_message(message)
    message.reject.assert_awaited_once_with(requeue=False)
    message.ack.assert_not_awaited()


@pytest.mark.asyncio
async def test_dependency_failure_requeues_command(monkeypatch):
    import app.broker.rabbitmq.consumer as module
    monkeypatch.setattr(module.asyncio, "sleep", AsyncMock())
    service = AsyncMock()
    service.process_image.side_effect = ConnectionError()
    message = AsyncMock()
    message.body = ProcessCommandEvent(command_id=uuid4(), command_type="image.process", file_id=uuid4(), original_key="a.png").model_dump_json().encode()
    await RabbitMQConsumer(None, service).handle_message(message)
    message.nack.assert_awaited_once_with(requeue=True)
    message.ack.assert_not_awaited()
