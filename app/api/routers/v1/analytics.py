from fastapi import APIRouter, Depends, Query

from app.api.dependencies import get_analytics_service
from app.services.analytics import AnalyticsService

router = APIRouter(prefix="/v1/analytics", tags=["Analytics"])


@router.get("/overview")
async def overview(service: AnalyticsService = Depends(get_analytics_service)) -> dict:
    return await service.overview()


@router.get("/uploads")
async def uploads(
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    service: AnalyticsService = Depends(get_analytics_service),
) -> list[dict]:
    return await service.uploads(page, page_size)


@router.get("/processing")
async def processing(
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    service: AnalyticsService = Depends(get_analytics_service),
) -> list[dict]:
    return await service.processing(page, page_size)
