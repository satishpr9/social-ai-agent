from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.user import UserRepository
from app.schemas.user import UserCreate, ProfileUpdate
from app.models.user import User
from app.models.profile import Profile
from app.core.security import get_password_hash, verify_password


class UserService:
    """
    Service layer class orchestrating business logic for Users and Profiles.
    Acts as the entrypoint for controllers to process transactions.
    """
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = UserRepository(db)

    async def register_user(self, user_in: UserCreate) -> User:
        """
        Business logic to register a new user and initialize their profile.
        Runs as an atomic transaction.
        """
        # Check if email is already taken
        existing_user = await self.repo.get_by_email(user_in.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A user with this email address already exists."
            )
            
        # Hash password and create User model
        hashed_password = get_password_hash(user_in.password)
        db_user = User(
            email=user_in.email,
            hashed_password=hashed_password,
            role="viewer" # Default registration role
        )
        await self.repo.create(db_user)
        
        # Create and link User Profile
        db_profile = Profile(
            user_id=db_user.id,
            full_name=user_in.full_name
        )
        await self.repo.create_profile(db_profile)
        
        # Commit transaction atomically
        await self.db.commit()
        await self.db.refresh(db_user)
        
        # Fetch the complete model (with profile joined) to return
        complete_user = await self.repo.get_by_id(db_user.id)
        if complete_user is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="User creation failed during profile load."
            )
        return complete_user

    async def authenticate_user(self, email: str, password: str) -> User:
        """
        Authenticates a user using email and password.
        """
        user = await self.repo.get_by_email(email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Incorrect email or password."
            )
            
        if not verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Incorrect email or password."
            )
            
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User account is deactivated."
            )
            
        return user

    async def update_profile(
        self,
        user: User,
        profile_in: ProfileUpdate
    ) -> Profile:
        """
        Updates profile fields for a user.
        """
        profile = user.profile
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found."
            )
            
        # Update fields dynamically if provided
        update_data = profile_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(profile, field, value)
            
        await self.repo.update_profile(profile)
        await self.db.commit()
        await self.db.refresh(profile)
        return profile
