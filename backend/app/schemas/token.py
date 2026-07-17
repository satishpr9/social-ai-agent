from pydantic import BaseModel


class Token(BaseModel):
    """
    Standard response structure containing the OAuth2 access and refresh tokens.
    """
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenRefreshRequest(BaseModel):
    """
    Payload required to request a new access token using a refresh token.
    """
    refresh_token: str
