from datetime import datetime

from pydantic import BaseModel, Field


class RefreshToken(BaseModel):
    id: str | None = None
    user_id: str
    jti: str
    expires_at: datetime
    is_revoked: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"from_attributes": True}
