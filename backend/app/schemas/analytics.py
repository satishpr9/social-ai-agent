from typing import List
from pydantic import BaseModel, ConfigDict


class PlatformMetric(BaseModel):
    platform: str
    views: int
    likes: int
    clicks: int

    model_config = ConfigDict(from_attributes=True)


class AnalyticsSummaryResponse(BaseModel):
    total_views: int
    total_likes: int
    total_clicks: int
    by_platform: List[PlatformMetric]

    model_config = ConfigDict(from_attributes=True)


class TrendDataPoint(BaseModel):
    date: str # Format: "YYYY-MM-DD"
    views: int
    likes: int
    clicks: int

    model_config = ConfigDict(from_attributes=True)


class AnalyticsTrendsResponse(BaseModel):
    trends: List[TrendDataPoint]

    model_config = ConfigDict(from_attributes=True)
