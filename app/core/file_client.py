import httpx


class FileClient:
    def __init__(self, base_url: str) -> None:
        self._client = httpx.AsyncClient(base_url=base_url, timeout=15)

    async def get_file(self, file_id: str) -> dict:
        response = await self._client.get(f"/v1/files/{file_id}")
        response.raise_for_status()
        return response.json()

    async def update_status(self, file_id: str, status: str, **payload) -> None:
        response = await self._client.patch(
            f"/internal/v1/files/{file_id}/{status}", json=payload,
        )
        response.raise_for_status()

    async def close(self) -> None:
        await self._client.aclose()
