from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.api.deps import get_current_user, RoleChecker
from app.models.user import User
from app.schemas.analytics import AnalyticsSummaryResponse, AnalyticsTrendsResponse
from app.services.analytics import AnalyticsService

router = APIRouter()

# Instantiate RBAC checker for database seeds
require_admin = Depends(RoleChecker(["admin"]))


@router.get("/summary", response_model=AnalyticsSummaryResponse)
async def get_analytics_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> AnalyticsSummaryResponse:
    """
    Retrieve overall totals of views, likes, and clicks, with platform breakdowns.
    """
    analytics_service = AnalyticsService(db)
    summary = await analytics_service.get_summary()
    return summary


@router.get("/trends", response_model=AnalyticsTrendsResponse)
async def get_analytics_trends(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> AnalyticsTrendsResponse:
    """
    Retrieve timeseries trends of views, likes, and clicks over a rolling window.
    """
    analytics_service = AnalyticsService(db)
    trends = await analytics_service.get_trends()
    return {"trends": trends}


@router.post("/seed", status_code=status.HTTP_201_CREATED, dependencies=[require_admin])
async def seed_mock_analytics(
    db: AsyncSession = Depends(get_db)
) -> dict:
    """
    Seeds mock timeseries metrics for local developer environment chart testing.
    Restricted to Admins.
    """
    analytics_service = AnalyticsService(db)
    await analytics_service.seed_mock_metrics()
    return {"status": "mock metrics seeded successfully"}
