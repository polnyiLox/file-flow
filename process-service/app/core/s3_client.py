from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from aiobotocore.session import get_session
from botocore.config import Config
from botocore.exceptions import ClientError

from .config import S3Settings


class S3Client:
    def __init__(self, settings: S3Settings) -> None:
        self._config = {
            "aws_access_key_id": settings.access_key,
            "aws_secret_access_key": settings.secret_key,
            "endpoint_url": settings.endpoint_url,
            "region_name": "us-east-1",
            "config": Config(signature_version="s3v4", s3={"addressing_style": "path"}),
        }
        self._public_endpoint_url = settings.public_endpoint_url
        self._bucket_name = settings.bucket_name
        self._presigned_url_ttl_seconds = settings.presigned_url_ttl_seconds
        self._session = get_session()

    @asynccontextmanager
    async def _get_client(self):
        async with self._session.create_client("s3", **self._config) as client:
            yield client

    async def ensure_bucket(self) -> None:
        async with self._get_client() as client:
            try:
                await client.head_bucket(Bucket=self._bucket_name)
            except ClientError as exc:
                if exc.response["Error"]["Code"] not in {"404", "NoSuchBucket"}:
                    raise
                await client.create_bucket(Bucket=self._bucket_name)

    async def upload_file(self, body: bytes, key: str, content_type: str = "application/octet-stream") -> None:
        async with self._get_client() as client:
            await client.put_object(
                Body=body, Bucket=self._bucket_name, Key=key, ContentType=content_type,
            )

    async def download_file(self, key: str) -> AsyncGenerator[bytes, None]:
        async with self._get_client() as client:
            response = await client.get_object(Bucket=self._bucket_name, Key=key)
            async with response["Body"] as body:
                while chunk := await body.read(65536):
                    yield chunk

    async def create_presigned_url(self, key: str) -> str:
        config = {**self._config, "endpoint_url": self._public_endpoint_url}
        async with self._session.create_client("s3", **config) as client:
            return await client.generate_presigned_url(
                "get_object", Params={"Bucket": self._bucket_name, "Key": key},
                ExpiresIn=self._presigned_url_ttl_seconds,
            )

    async def delete_file(self, key: str) -> None:
        async with self._get_client() as client:
            await client.delete_object(Bucket=self._bucket_name, Key=key)
