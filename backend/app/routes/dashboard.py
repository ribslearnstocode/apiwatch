from fastapi import APIRouter, Depends, Query

from ..dependencies import get_analytics_service
from ..schemas import Summary
from ..services.analytics import AnalyticsService

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("/summary", response_model=Summary)
def summary(hours: int = Query(24, ge=1, le=720), service: AnalyticsService = Depends(get_analytics_service)):
    return service.summary(hours)
