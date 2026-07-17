from datetime import datetime, timedelta, timezone
from typing import Any, Union
import bcrypt

# Monkeypatch bcrypt to maintain passlib compatibility (bcrypt >= 4.0.0 on Python 3.12+)
# Bcrypt natively truncates passwords to 72 bytes. Modern Python bindings raise a ValueError
# instead of truncating. We manually truncate here to match specs and bypass passlib init checks.
_orig_hashpw = bcrypt.hashpw
def _patched_hashpw(password, salt):
    p_bytes = password.encode("utf-8") if isinstance(password, str) else password
    if len(p_bytes) > 72:
        p_bytes = p_bytes[:72]
    return _orig_hashpw(p_bytes, salt)

_orig_checkpw = bcrypt.checkpw
def _patched_checkpw(password, hashed):
    p_bytes = password.encode("utf-8") if isinstance(password, str) else password
    if len(p_bytes) > 72:
        p_bytes = p_bytes[:72]
    return _orig_checkpw(p_bytes, hashed)

bcrypt.hashpw = _patched_hashpw
bcrypt.checkpw = _patched_checkpw

from jose import jwt
from passlib.context import CryptContext
from app.core.config import settings

# Setup password hashing context using Bcrypt.
# passlib handles automatic salting and formatting.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifies that a plain text password matches its stored bcrypt hash.
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Generates a secure salted bcrypt hash of a plain text password.
    """
    return pwd_context.hash(password)


def create_access_token(
    subject: Union[str, Any],
    role: str,
    expires_delta: timedelta = None
) -> str:
    """
    Generates a signed JWT Access Token containing user ID (subject) and user role.
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    # Payload includes standard claims:
    # exp (expiration time), sub (subject/user ID), and role
    to_encode = {
        "exp": int(expire.timestamp()),
        "sub": str(subject),
        "role": role,
        "type": "access"
    }
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


def create_refresh_token(
    subject: Union[str, Any],
    expires_delta: timedelta = None
) -> str:
    """
    Generates a signed JWT Refresh Token with longer lifetime.
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
    
    to_encode = {
        "exp": int(expire.timestamp()),
        "sub": str(subject),
        "type": "refresh"
    }
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt
