from fastapi import Request

from app.services.analytics import AnalyticsService


def get_analytics_service(request: Request) -> AnalyticsService:
    return request.app.state.analytics_service
