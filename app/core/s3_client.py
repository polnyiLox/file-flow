from contextlib import asynccontextmanager
from typing import AsyncGenerator

from aiobotocore.session import get_session

from .config import S3Settings


class S3Client:
    def __init__(self, settings: S3Settings) -> None:
        self._config = {
            "aws_access_key_id": settings.access_key,
            "aws_secret_access_key": settings.secret_key,
            "endpoint_url": settings.endpoint_url,
        }
        self._bucket_name = settings.bucket_name
        self._presigned_url_ttl_seconds = settings.presigned_url_ttl_seconds
        self._session = get_session()

    @asynccontextmanager
    async def _get_client(self):
        async with self._session.create_client("s3", **self._config) as client:
            yield client

    async def upload_file(
            self,
            body: bytes,
            key: str,
            bucket_name: str | None = None
    ) -> None:
        async with self._get_client() as client:
            await client.put_object(
                Body=body,
                Bucket=bucket_name or self._bucket_name,
                Key=key
            )

    async def download_file(self, key: str, bucket_name: str | None = None) -> AsyncGenerator[bytes, None]:
        async with self._get_client() as client:
            response = await client.get_object(
                Bucket=bucket_name or self._bucket_name,
                Key=key
            )

            file = response["Body"]
            try:
                while True:
                    chunk = await file.read(1024)

                    if chunk is None:
                        break

                    yield chunk
            finally:
                await file.close()

    async def create_presigned_url(
            self,
            key: str,
            bucket_name: str | None = None,
            ttl_seconds: int | None = None,
    ) -> str:
        async with self._get_client() as client:
            url = await client.generate_presigned_url(
                'get_object',
                Params={'Bucket': bucket_name or self._bucket_name, 'Key': key},
                ExpiresIn=ttl_seconds or self._presigned_url_ttl_seconds
            )
            return url

    async def delete_file(
            self,
            key: str,
            bucket_name: str | None = None
    ) -> None:
        async with self._get_client() as client:
            await client.delete_object(
                Bucket=bucket_name or self._bucket_name,
                Key=key
            )