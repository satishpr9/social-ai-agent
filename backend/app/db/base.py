# Import all models so that Base has them registered on Base.metadata
# before being imported by Alembic migrations
from app.db.base_class import Base  # noqa
from app.models.user import User  # noqa
from app.models.profile import Profile  # noqa
from app.models.post import SocialPost  # noqa
from app.models.approval import ApprovalRequest  # noqa
from app.models.analytics import AnalyticsMetric  # noqa
from app.models.lead import Lead  # noqa
