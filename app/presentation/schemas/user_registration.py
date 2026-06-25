from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class UserRegistrationCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=30)
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=200)
    password: str = Field(..., min_length=6, max_length=128)


class UserLoginRequest(BaseModel):
    username_or_email: str = Field(..., min_length=3)
    password: str = Field(..., min_length=6)


class UserRegistrationResponse(BaseModel):
    id: str
    username: str
    email: EmailStr
    full_name: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in_minutes: int
    refresh_expires_in_days: int
    user: UserRegistrationResponse


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., min_length=10)
