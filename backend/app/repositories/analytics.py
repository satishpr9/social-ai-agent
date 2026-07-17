import uuid
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any
from sqlalchemy import func, select, cast, Date, text
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.analytics import AnalyticsMetric


class AnalyticsRepository:
    """
    Repository class encapsulating database operations for AnalyticsMetrics.
    """
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def add_metric(
        self,
        post_id: uuid.UUID | None,
        metric_type: str,
        platform: str,
        value: int = 1
    ) -> AnalyticsMetric:
        """
        Records a new analytics metric entry in the database.
        """
        metric = AnalyticsMetric(
            post_id=post_id,
            metric_type=metric_type,
            platform=platform,
            metric_value=value,
            timestamp=datetime.now(timezone.utc)
        )
        self.db.add(metric)
        await self.db.flush()
        return metric

    async def get_summary_metrics(self) -> Dict[str, Any]:
        """
        Aggregates total summary metrics (views, likes, clicks) and provides
        a platform breakdown by executing grouped sum selects.
        """
        # 1. Query overall totals by metric_type
        total_stmt = (
            select(
                AnalyticsMetric.metric_type,
                func.sum(AnalyticsMetric.metric_value)
            )
            .group_by(AnalyticsMetric.metric_type)
        )
        total_result = await self.db.execute(total_stmt)
        
        totals = {"views": 0, "likes": 0, "clicks": 0}
        for metric_type, val_sum in total_result.all():
            if metric_type in totals:
                totals[metric_type] = int(val_sum or 0)

        # 2. Query breakdown grouped by platform and metric_type
        platform_stmt = (
            select(
                AnalyticsMetric.platform,
                AnalyticsMetric.metric_type,
                func.sum(AnalyticsMetric.metric_value)
            )
            .group_by(AnalyticsMetric.platform, AnalyticsMetric.metric_type)
        )
        platform_result = await self.db.execute(platform_stmt)

        platform_map: Dict[str, Dict[str, int]] = {}
        for platform, metric_type, val_sum in platform_result.all():
            if platform not in platform_map:
                platform_map[platform] = {"views": 0, "likes": 0, "clicks": 0}
            if metric_type in platform_map[platform]:
                platform_map[platform][metric_type] = int(val_sum or 0)

        by_platform_list = []
        for plat, metrics in platform_map.items():
            by_platform_list.append({
                "platform": plat,
                "views": metrics["views"],
                "likes": metrics["likes"],
                "clicks": metrics["clicks"]
            })

        return {
            "total_views": totals["views"],
            "total_likes": totals["likes"],
            "total_clicks": totals["clicks"],
            "by_platform": by_platform_list
        }

    async def get_trends_metrics(self, days: int = 30) -> List[Dict[str, Any]]:
        """
        Retrieves daily timeseries performance metrics over a rolling window.
        """
        start_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        # Cast timestamp to SQL Date to truncate hours/minutes/seconds
        stmt = (
            select(
                cast(AnalyticsMetric.timestamp, Date).label("date_day"),
                AnalyticsMetric.metric_type,
                func.sum(AnalyticsMetric.metric_value)
            )
            .filter(AnalyticsMetric.timestamp >= start_date)
            .group_by(text("date_day"), AnalyticsMetric.metric_type)
            .order_by(text("date_day").asc())
        )
        result = await self.db.execute(stmt)

        # Map rows into a clean timeseries structure
        daily_trends: Dict[str, Dict[str, int]] = {}
        for date_day, metric_type, val_sum in result.all():
            # date_day returns a datetime.date object, we convert to string format YYYY-MM-DD
            date_str = date_day.strftime("%Y-%m-%d")
            if date_str not in daily_trends:
                daily_trends[date_str] = {"views": 0, "likes": 0, "clicks": 0}
            if metric_type in daily_trends[date_str]:
                daily_trends[date_str][metric_type] = int(val_sum or 0)

        trends_list = []
        # Sort keys to ensure chronological timeseries output
        for d_str in sorted(daily_trends.keys()):
            metrics = daily_trends[d_str]
            trends_list.append({
                "date": d_str,
                "views": metrics["views"],
                "likes": metrics["likes"],
                "clicks": metrics["clicks"]
            })

        return trends_list
ActiveUser = "User"
