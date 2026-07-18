import uuid
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from pydantic import BaseModel, ValidationError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload

from app.core.config import settings
from app.db.session import get_db
from app.models.user import User

# Define the OAuth2 security scheme pointing to the login route
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login"
)


class TokenPayload(BaseModel):
    """
    Pydantic model representing decoded JWT payload claims.
    """
    sub: str | None = None
    role: str | None = None
    type: str | None = None


async def get_current_user(
    db: AsyncSession = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> User:
    """
    Dependency that decodes the JWT access token, validates the signature,
    checks expiration, and retrieves the authenticated user from the database.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decode the token cryptographically
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        
        token_data = TokenPayload(
            sub=payload.get("sub"),
            role=payload.get("role"),
            type=payload.get("type")
        )
        
        # Enforce that refresh tokens cannot be used to authenticate access routes
        if token_data.type == "refresh":
            raise credentials_exception
            
        if token_data.sub is None:
            raise credentials_exception
            
    except (JWTError, ValidationError):
        raise credentials_exception
        
    # Retrieve the user record asynchronously from PostgreSQL/SQLite
    try:
        sub_uuid = uuid.UUID(token_data.sub)
    except ValueError:
        raise credentials_exception

    result = await db.execute(
        select(User)
        .options(joinedload(User.profile))
        .filter(User.id == sub_uuid)
    )
    user = result.scalars().first()
    
    if user is None:
        raise credentials_exception
        
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
        
    return user


class RoleChecker:
    """
    Dependency factory class for Role-Based Access Control (RBAC).
    """
    def __init__(self, allowed_roles: list[str]) -> None:
        self.allowed_roles = allowed_roles

    def __call__(
        self,
        current_user: User = Depends(get_current_user)
    ) -> User:
        """
        Validates that the authenticated user has an authorized role.
        """
        if current_user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this resource"
            )
        return current_user
