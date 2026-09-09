from fastapi import APIRouter

from app.core.config import settings

from .file import router as file_router


router = APIRouter(
    prefix=settings.api.v1_prefix
)
router.include_router(file_router)