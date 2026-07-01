from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.domain.enums import AccountNature, AccountType


class ChartOfAccount(BaseModel):
    id: str | None = None
    company_id: str
    code: str
    name: str
    account_type: AccountType
    nature: AccountNature
    parent_id: str | None = None
    level: int = 1
    is_group: bool = False
    is_active: bool = True
    opening_balance: Decimal = Field(default=Decimal("0.00"), decimal_places=2)
    current_balance: Decimal = Field(default=Decimal("0.00"), decimal_places=2)
    description: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"from_attributes": True}
