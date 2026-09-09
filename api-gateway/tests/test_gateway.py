import httpx
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.service_client import forwarded_headers


def test_hop_headers_are_removed():
    assert forwarded_headers({"connection": "x-secret", "x-secret": "value", "content-type": "image/png"}) == {"content-type": "image/png"}


def test_proxy_preserves_query_body_and_status():
    seen = []
    def upstream(request):
        seen.append(request)
        return httpx.Response(201, json={"id": "file-id"})
    with TestClient(app) as client:
        app.state.files._client = httpx.AsyncClient(transport=httpx.MockTransport(upstream), base_url="http://files")
        response = client.post("/api/v1/files?a=1&a=2", content=b"image", headers={"content-type": "image/png"})
    assert response.status_code == 201
    assert seen[0].url.path == "/v1/files"
    assert seen[0].url.query == b"a=1&a=2"
    assert seen[0].content == b"image"


def test_internal_routes_are_not_exposed():
    with TestClient(app) as client:
        assert client.patch("/internal/v1/files/123/processed").status_code == 404
        assert client.get("/api/v1/analytics/unknown").status_code == 404


@pytest.mark.parametrize("error,status", [(httpx.ConnectError("offline"), 502), (httpx.ReadTimeout("slow"), 504)])
def test_upstream_failures(error, status):
    def upstream(request):
        raise error
    with TestClient(app) as client:
        app.state.files._client = httpx.AsyncClient(transport=httpx.MockTransport(upstream), base_url="http://files")
        assert client.get("/api/v1/files").status_code == status


def test_gateway_limits_request_body():
    with TestClient(app) as client:
        app.state.files._max_body_size = 3
        assert client.post("/api/v1/files", content=b"1234").status_code == 413
