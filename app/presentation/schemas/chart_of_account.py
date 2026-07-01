from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.domain.enums import AccountNature, AccountType


class ChartOfAccountCreate(BaseModel):
    code: str = Field(..., min_length=1, max_length=20)
    name: str = Field(..., min_length=1, max_length=200)
    account_type: AccountType
    nature: AccountNature | None = None
    parent_id: str | None = None
    is_group: bool = False
    is_active: bool = True
    opening_balance: Decimal = Field(default=Decimal("0.00"), ge=0)
    description: str | None = None


class ChartOfAccountUpdate(BaseModel):
    code: str | None = Field(None, min_length=1, max_length=20)
    name: str | None = Field(None, min_length=1, max_length=200)
    account_type: AccountType | None = None
    parent_id: str | None = None
    is_group: bool | None = None
    is_active: bool | None = None
    opening_balance: Decimal | None = None
    description: str | None = None


class ChartOfAccountResponse(BaseModel):
    id: str
    company_id: str
    code: str
    name: str
    account_type: AccountType
    nature: AccountNature
    parent_id: str | None
    level: int
    is_group: bool
    is_active: bool
    opening_balance: Decimal
    current_balance: Decimal
    description: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
