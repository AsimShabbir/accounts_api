from datetime import date, datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field

from app.domain.enums import ReportType


class ReportLineItem(BaseModel):
    account_id: str | None = None
    account_code: str
    account_name: str
    account_type: str | None = None
    debit: Decimal = Field(default=Decimal("0.00"), decimal_places=2)
    credit: Decimal = Field(default=Decimal("0.00"), decimal_places=2)
    balance: Decimal = Field(default=Decimal("0.00"), decimal_places=2)
    metadata: dict[str, Any] = Field(default_factory=dict)


class FinancialReport(BaseModel):
    id: str | None = None
    report_type: ReportType
    report_title: str
    from_date: date | None = None
    to_date: date | None = None
    report_date: date
    account_id: str | None = None
    account_code: str | None = None
    line_items: list[ReportLineItem] = Field(default_factory=list)
    totals: dict[str, Decimal] = Field(default_factory=dict)
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    parameters: dict[str, Any] = Field(default_factory=dict)

    model_config = {"from_attributes": True}
