import httpx
from fastapi import HTTPException, Request
from starlette.responses import Response

HOP_HEADERS = {
    "connection", "keep-alive", "proxy-authenticate", "proxy-authorization",
    "te", "trailer", "transfer-encoding", "upgrade", "host", "content-length",
}


def forwarded_headers(headers) -> dict:
    excluded = HOP_HEADERS | {
        name.strip().lower() for name in headers.get("connection", "").split(",")
    }
    return {key: value for key, value in headers.items() if key.lower() not in excluded}


class ServiceClient:
    def __init__(self, base_url: str, timeout: float, max_body_size: int) -> None:
        self._client = httpx.AsyncClient(base_url=base_url, timeout=timeout)
        self._max_body_size = max_body_size

    async def forward(self, request: Request, path: str) -> Response:
        body = bytearray()
        async for chunk in request.stream():
            body.extend(chunk)
            if len(body) > self._max_body_size:
                raise HTTPException(413, "Request body is too large")
        try:
            response = await self._client.request(
                request.method, path, params=request.query_params.multi_items(),
                headers=forwarded_headers(request.headers), content=bytes(body),
            )
        except httpx.TimeoutException as exc:
            raise HTTPException(504, "Service request timed out") from exc
        except httpx.RequestError as exc:
            raise HTTPException(502, "Service is unavailable") from exc
        headers = forwarded_headers(response.headers)
        # httpx already decompresses response.content.
        headers.pop("content-encoding", None)
        return Response(response.content, status_code=response.status_code, headers=headers)

    async def close(self) -> None:
        await self._client.aclose()
