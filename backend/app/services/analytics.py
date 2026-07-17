import uuid
import random
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.analytics import AnalyticsRepository
from app.models.analytics import AnalyticsMetric


class AnalyticsService:
    """
    Business service layer orchestrating analytics events tracking,
    aggregations, and developer seeding utilities.
    """
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = AnalyticsRepository(db)

    async def track_event(
        self,
        post_id: uuid.UUID | None,
        metric_type: str,
        platform: str,
        value: int = 1
    ) -> None:
        """
        Validates the event type and records it.
        """
        valid_types = ["views", "likes", "clicks"]
        if metric_type not in valid_types:
            raise ValueError(f"Invalid metric type. Must be one of {valid_types}.")

        valid_platforms = ["linkedin", "twitter", "facebook", "instagram"]
        if platform not in valid_platforms:
            raise ValueError(f"Invalid platform name. Must be one of {valid_platforms}.")

        await self.repo.add_metric(
            post_id=post_id,
            metric_type=metric_type,
            platform=platform,
            value=value
        )
        await self.db.commit()

    async def get_summary(self) -> Dict[str, Any]:
        """
        Retrieves the aggregated KPI summaries and platform breakdowns.
        """
        summary = await self.repo.get_summary_metrics()
        
        # If database is fresh and contains no metrics, return clean default representations
        if not summary["by_platform"]:
            summary["by_platform"] = [
                {"platform": "linkedin", "views": 0, "likes": 0, "clicks": 0},
                {"platform": "twitter", "views": 0, "likes": 0, "clicks": 0},
                {"platform": "facebook", "views": 0, "likes": 0, "clicks": 0},
                {"platform": "instagram", "views": 0, "likes": 0, "clicks": 0}
            ]
        return summary

    async def get_trends(self) -> List[Dict[str, Any]]:
        """
        Retrieves the chronologically sorted daily trends for plotting charts.
        """
        trends = await self.repo.get_trends_metrics()
        
        # If empty, return a baseline mock 7-day flatline trend
        if not trends:
            now = datetime.now(timezone.utc)
            for i in range(7, 0, -1):
                d_str = (now - timedelta(days=i)).strftime("%Y-%m-%d")
                trends.append({
                    "date": d_str,
                    "views": 0,
                    "likes": 0,
                    "clicks": 0
                })
        return trends

    async def seed_mock_metrics(self) -> None:
        """
        Generates 30 days of realistic, upward-trending marketing engagement metrics.
        Used for local development dashboard styling and chart verification.
        """
        platforms = ["linkedin", "twitter", "facebook", "instagram"]
        metric_types = ["views", "likes", "clicks"]
        now = datetime.now(timezone.utc)

        # Baseline coefficients for platforms
        plat_coeff = {
            "linkedin": {"views": 15, "likes": 3, "clicks": 2},
            "twitter": {"views": 25, "likes": 4, "clicks": 3},
            "facebook": {"views": 10, "likes": 2, "clicks": 1},
            "instagram": {"views": 20, "likes": 6, "clicks": 2}
        }

        # Clear existing metrics for fresh seed
        # (Usually for local dev sandbox databases only)
        # We write raw insert calls to construct the historical timeseries
        for i in range(30, 0, -1):
            target_date = now - timedelta(days=i)
            # Create a slight upward multiplier over the 30 days
            trend_multiplier = 1.0 + (30 - i) * 0.05

            for platform in platforms:
                for metric_type in metric_types:
                    base = plat_coeff[platform][metric_type]
                    # Add random noise around the trend
                    val = int(base * trend_multiplier * random.uniform(0.7, 1.3))
                    if val <= 0:
                        val = 1
                        
                    metric = AnalyticsMetric(
                        metric_type=metric_type,
                        platform=platform,
                        metric_value=val,
                        timestamp=target_date
                    )
                    self.db.add(metric)
                    
        await self.db.commit()
ActiveUser = "User"
