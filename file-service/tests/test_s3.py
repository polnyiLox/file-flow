from unittest.mock import AsyncMock, MagicMock

from dotenv import load_dotenv
load_dotenv(".env.example", override=True)

import pytest
from app.core.config import settings
from app.core.s3_client import S3Client


@pytest.mark.asyncio
async def test_download_stops_at_eof_and_closes_stream():
    client = S3Client(settings.s3)
    body = AsyncMock()
    body.__aenter__.return_value = body
    body.read.side_effect = [b"image", b""]
    s3 = AsyncMock()
    s3.get_object.return_value = {"Body": body}
    context = AsyncMock()
    context.__aenter__.return_value = s3
    client._get_client = MagicMock(return_value=context)
    assert [chunk async for chunk in client.download_file("original.png")] == [b"image"]
    assert body.read.await_count == 2
    body.__aexit__.assert_awaited_once()
