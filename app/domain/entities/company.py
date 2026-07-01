from datetime import datetime

from pydantic import BaseModel, Field


class Company(BaseModel):
    id: str | None = None
    company_id: str
    name: str
    address: str
    logo: str
    favicon: str
    user_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"from_attributes": True}
