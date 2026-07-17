import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from app.models.user import User
from app.models.profile import Profile


class UserRepository:
    """
    Repository class encapsulating database operations for Users and Profiles.
    Follows the Repository Pattern to decouple data access from business services.
    """
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        """
        Retrieves a user by UUID with their profile eagerly loaded.
        """
        stmt = (
            select(User)
            .options(joinedload(User.profile))
            .filter(User.id == user_id)
        )
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def get_by_email(self, email: str) -> User | None:
        """
        Retrieves a user by email address with their profile eagerly loaded.
        """
        stmt = (
            select(User)
            .options(joinedload(User.profile))
            .filter(User.email == email)
        )
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def create(self, user: User) -> User:
        """
        Persists a user object to the database.
        """
        self.db.add(user)
        await self.db.flush() # Flush to generate IDs and default database values
        return user

    async def update(self, user: User) -> User:
        """
        Updates an existing user record.
        """
        self.db.add(user)
        await self.db.flush()
        return user

    async def create_profile(self, profile: Profile) -> Profile:
        """
        Persists a profile object to the database.
        """
        self.db.add(profile)
        await self.db.flush()
        return profile

    async def update_profile(self, profile: Profile) -> Profile:
        """
        Updates an existing profile record.
        """
        self.db.add(profile)
        await self.db.flush()
        return profile
