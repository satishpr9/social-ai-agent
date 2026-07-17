from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse, ProfileUpdate, ProfileResponse
from app.services.user import UserService

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db)
) -> UserResponse:
    """
    Register a new user and automatically attach a blank profile.
    """
    user_service = UserService(db)
    user = await user_service.register_user(user_in)
    return user


@router.get("/me", response_model=UserResponse)
async def get_my_details(
    current_user: User = Depends(get_current_user)
) -> UserResponse:
    """
    Retrieve details of the currently authenticated user session.
    """
    return current_user


@router.put("/me/profile", response_model=ProfileResponse)
async def update_my_profile(
    profile_in: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> ProfileResponse:
    """
    Update the profile information of the current authenticated user.
    """
    user_service = UserService(db)
    updated_profile = await user_service.update_profile(
        user=current_user,
        profile_in=profile_in
    )
    return updated_profile
