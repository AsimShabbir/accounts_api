from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class UserRegistration(BaseModel):
    id: str | None = None
    username: str
    email: EmailStr
    full_name: str
    password_hash: str
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"from_attributes": True}
