from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.core.config import settings
from app.core.service_client import ServiceClient
from app.core.logging import configure_logging
from app.core.metrics import setup_metrics

configure_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.files = ServiceClient(settings.file_service_url, settings.timeout_seconds, settings.max_body_size)
    app.state.analytics = ServiceClient(settings.analytics_service_url, settings.timeout_seconds, settings.max_body_size)
    try:
        yield
    finally:
        await app.state.files.close()
        await app.state.analytics.close()


app = FastAPI(title="FileFlow Gateway", lifespan=lifespan)
setup_metrics(app)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.api_route("/api/v1/files", methods=["GET", "POST"])
@app.api_route("/api/v1/files/{path:path}", methods=["GET", "DELETE"])
async def files(request: Request, path: str = ""):
    target = "/v1/files" + (f"/{path}" if path else "")
    return await request.app.state.files.forward(request, target)


@app.get("/api/v1/analytics/{report}")
async def analytics(request: Request, report: str):
    from fastapi import HTTPException
    if report not in {"overview", "uploads", "processing"}:
        raise HTTPException(404, "Unknown report")
    return await request.app.state.analytics.forward(request, f"/v1/analytics/{report}")


static_directory = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=static_directory), name="static")


@app.get("/", include_in_schema=False)
async def frontend() -> FileResponse:
    return FileResponse(static_directory / "index.html")
