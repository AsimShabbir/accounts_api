from datetime import datetime

from pydantic import BaseModel, Field


class CompanyCreate(BaseModel):
    slug: str = Field(
        ...,
        min_length=1,
        max_length=50,
        pattern=r"^[a-zA-Z0-9_-]+$",
        description="Unique company slug (e.g. ahsoftech)",
    )
    name: str = Field(..., min_length=1, max_length=200)
    address: str = Field(..., min_length=1, max_length=500)
    logo: str = Field(..., min_length=1, max_length=500)
    favicon: str = Field(..., min_length=1, max_length=500)


class CompanyUpdate(BaseModel):
    slug: str | None = Field(
        None,
        min_length=1,
        max_length=50,
        pattern=r"^[a-zA-Z0-9_-]+$",
        description="Unique company slug (e.g. ahsoftech)",
    )
    name: str | None = Field(None, min_length=1, max_length=200)
    address: str | None = Field(None, min_length=1, max_length=500)
    logo: str | None = Field(None, min_length=1, max_length=500)
    favicon: str | None = Field(None, min_length=1, max_length=500)


class CompanyResponse(BaseModel):
    id: str = Field(..., description="Company document id — use as company_id in API calls")
    slug: str = Field(..., description="Company slug (e.g. ahsoftech) — display only, not for API company_id")
    name: str
    address: str
    logo: str
    favicon: str
    user_id: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

    @classmethod
    def from_company(cls, company) -> "CompanyResponse":
        return cls(
            id=company.id or "",
            slug=company.company_id,
            name=company.name,
            address=company.address,
            logo=company.logo,
            favicon=company.favicon,
            user_id=company.user_id,
            created_at=company.created_at,
            updated_at=company.updated_at,
        )
