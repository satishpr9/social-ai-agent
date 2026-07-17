import re
from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase, declared_attr

# Naming convention for database constraints.
# Standardizes naming across all DB migrations, preventing Alembic conflicts.
POSTGRES_NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

metadata = MetaData(naming_convention=POSTGRES_NAMING_CONVENTION)


class Base(DeclarativeBase):
    """
    SQLAlchemy 2.0 Declarative Base.
    Registers our database metadata and automatically maps model class names
    to snake_case table names.
    """
    metadata = metadata

    @declared_attr.directive
    def __tablename__(cls) -> str:
        """
        Automatically generates tablename from class name.
        Example:
            User -> users
            SocialPost -> social_posts
            AnalyticsMetric -> analytics_metrics
        """
        # Convert CamelCase to snake_case
        snake_name = re.sub(r'(?<!^)(?=[A-Z])', '_', cls.__name__).lower()
        
        # Append "s" or "es" for pluralization
        if snake_name.endswith('y'):
            return f"{snake_name[:-1]}ies"
        elif snake_name.endswith(('s', 'x', 'z', 'ch', 'sh')):
            return f"{snake_name}es"
        else:
            return f"{snake_name}s"
