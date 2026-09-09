import asyncio
from io import BytesIO
import logging
from time import perf_counter
import warnings

import httpx
from PIL import Image, ImageOps, UnidentifiedImageError

from app.core.metrics import images_processed, processing_failed, processing_duration

logger = logging.getLogger(__name__)


class ProcessService:
    def __init__(self, s3_client, file_client, kafka_producer, thumbnail_size: int = 400) -> None:
        self._s3_client = s3_client
        self._file_client = file_client
        self._kafka_producer = kafka_producer
        self._thumbnail_size = thumbnail_size

    def create_thumbnail(self, body: bytes) -> bytes:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(BytesIO(body)) as image:
                if image.format not in {"JPEG", "PNG"}:
                    raise ValueError("Only JPEG and PNG images are allowed")
                image = ImageOps.exif_transpose(image)
                image.thumbnail((self._thumbnail_size, self._thumbnail_size))
                output = BytesIO()
                image.convert("RGB").save(output, format="JPEG")
                return output.getvalue()

    async def process_image(self, command) -> None:
        file_id = str(command.file_id)
        started = perf_counter()
        try:
            file = await self._file_client.get_file(file_id)
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404:
                return
            raise
        if command.original_key != file["original_key"]:
            raise ValueError("Command original key does not match file metadata")
        if file["status"] == "FAILED":
            await self._kafka_producer.publish_event(command, "file.processing_failed")
            return
        thumbnail_key = f"files/{file_id}/thumbnail.jpg"
        if file["status"] != "READY":
            await self._file_client.update_status(file_id, "processing")
            await self._kafka_producer.publish_event(command, "file.processing_started")
            body = b"".join([chunk async for chunk in self._s3_client.download_file(command.original_key)])
            try:
                thumbnail = await asyncio.to_thread(self.create_thumbnail, body)
            except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError, Image.DecompressionBombWarning):
                await self._file_client.update_status(file_id, "failed")
                await self._kafka_producer.publish_event(command, "file.processing_failed")
                processing_failed.inc()
                logger.exception("Image processing failed file_id=%s command_id=%s", file_id, command.command_id)
                return
            await self._s3_client.upload_file(thumbnail, thumbnail_key, "image/jpeg")
            await self._file_client.update_status(file_id, "processed", thumbnail_key=thumbnail_key)
        elapsed = perf_counter() - started
        payload = {"thumbnail_key": thumbnail_key}
        # A retry after READY does not measure the original processing duration.
        if file["status"] != "READY":
            payload["processing_time_ms"] = round(elapsed * 1000)
        await self._kafka_producer.publish_event(command, "file.processed", **payload)
        images_processed.inc()
        processing_duration.observe(elapsed)
        logger.info("Image processed file_id=%s command_id=%s processing_ms=%s", file_id, command.command_id, round(elapsed * 1000))
