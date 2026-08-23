from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routers import v1_router
from app.core.config import settings
from app.core.health import router as health_router
from app.db import mongodb_client
from app.exceptions import AppError


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    await mongodb_client.connect()
    try:
        yield
    finally:
        await mongodb_client.close()


app = FastAPI(lifespan=lifespan)

app.include_router(v1_router)
app.include_router(health_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.middleware.allow_origins,
    allow_methods=settings.middleware.allow_methods,
    allow_headers=settings.middleware.allow_headers,
    allow_credentials=settings.middleware.allow_credentials,
)


@app.exception_handler(AppError)
async def app_error_handler(_: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )
