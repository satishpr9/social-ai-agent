from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_db
from app.core.security import create_access_token, create_refresh_token
from app.services.user import UserService
from app.schemas.token import Token, TokenRefreshRequest

router = APIRouter()


@router.post("/login", response_model=Token)
async def login(
    db: AsyncSession = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Token:
    """
    OAuth2 compatible token login, returning access and refresh tokens.
    """
    user_service = UserService(db)
    # OAuth2 forms map the email input to 'form_data.username'
    user = await user_service.authenticate_user(
        email=form_data.username,
        password=form_data.password
    )
    
    # Generate token payload signatures
    access_token = create_access_token(subject=user.id, role=user.role)
    refresh_token = create_refresh_token(subject=user.id)
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token
    )


@router.post("/refresh", response_model=Token)
async def refresh_token(
    request_data: TokenRefreshRequest,
    db: AsyncSession = Depends(get_db)
) -> Token:
    """
    Exchange a valid JWT Refresh Token for a fresh access token.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate refresh credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decode and inspect the refresh token
        payload = jwt.decode(
            request_data.refresh_token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        user_id: str = payload.get("sub")
        token_type: str = payload.get("type")
        
        if user_id is None or token_type != "refresh":
            raise credentials_exception
            
    except JWTError:
        raise credentials_exception
        
    user_service = UserService(db)
    user = await user_service.repo.get_by_id(user_id)
    
    if user is None or not user.is_active:
        raise credentials_exception
        
    # Issue a new access token and keep the refresh cycle active
    new_access_token = create_access_token(subject=user.id, role=user.role)
    new_refresh_token = create_refresh_token(subject=user.id)
    
    return Token(
        access_token=new_access_token,
        refresh_token=new_refresh_token
    )
