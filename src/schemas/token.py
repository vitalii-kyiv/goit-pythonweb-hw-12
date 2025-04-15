from pydantic import BaseModel


class TokenResponse(BaseModel):
    """
    Schema representing the response returned after a successful authentication.
    """
    access_token: str
    token_type: str = "bearer"
    refresh_token: str


class RefreshTokenRequest(BaseModel):
    """
    Schema representing a request to refresh an access token using a refresh token.
    """
    refresh_token: str
