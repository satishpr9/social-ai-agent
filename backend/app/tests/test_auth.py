import pytest
from jose import jwt

from app.core.config import settings
from app.core.security import get_password_hash, verify_password, create_access_token, create_refresh_token


def test_password_hashing() -> None:
    """
    Unit test: Verifies that password hashing generates secure keys
    and that matching strings verify correctly.
    """
    password = "secret_password_123"
    hashed = get_password_hash(password)
    
    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("wrong_password", hashed) is False


def test_token_generation() -> None:
    """
    Unit test: Verifies JWT Access and Refresh token generation payload structures.
    """
    subject_id = "12345678-1234-5678-1234-567812345678"
    role = "editor"
    
    access_token = create_access_token(subject=subject_id, role=role)
    refresh_token = create_refresh_token(subject=subject_id)
    
    # Decode and verify access payload
    access_payload = jwt.decode(access_token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    assert access_payload["sub"] == subject_id
    assert access_payload["role"] == role
    assert access_payload["type"] == "access"
    
    # Decode and verify refresh payload
    refresh_payload = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    assert refresh_payload["sub"] == subject_id
    assert refresh_payload["type"] == "refresh"


@pytest.mark.asyncio
async def test_user_registration_and_login_flow(client) -> None:
    """
    Integration test: Registers a new user account and authenticates via login endpoint.
    """
    email = "new_user@socialagent.ai"
    password = "secure_password_abc"
    
    # 1. Register User
    register_payload = {
        "email": email,
        "password": password,
        "full_name": "Satish Auth Test"
    }
    
    register_response = await client.post("/v1/users/register", json=register_payload)
    assert register_response.status_code == 201
    
    data = register_response.json()
    assert data["email"] == email
    assert data["role"] == "viewer"
    assert "id" in data

    # 2. Login User (OAuth2PasswordRequestForm expects data parameter form payload)
    login_data = {
        "username": email,
        "password": password
    }
    
    login_response = await client.post(
        "/v1/auth/login",
        data=login_data
    )
    assert login_response.status_code == 200
    
    token_data = login_response.json()
    assert "access_token" in token_data
    assert "refresh_token" in token_data
    assert token_data["token_type"] == "bearer"
