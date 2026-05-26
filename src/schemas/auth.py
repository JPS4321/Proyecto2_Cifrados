# src/schemas/auth.py

from pydantic import BaseModel, EmailStr, Field

class RegisterRequest(BaseModel):
    display_name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)

class RegisterResponse(BaseModel):
    message: str
    user_id: str
    email: EmailStr
    display_name: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    totp_code: str | None = None

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class RefreshTokenRequest(BaseModel):
    refresh_token: str