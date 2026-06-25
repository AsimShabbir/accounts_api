from datetime import date, datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel

from app.domain.enums import ReportType


class ReportLineItemResponse(BaseModel):
    account_id: str | None
    account_code: str
    account_name: str
    account_type: str | None
    debit: Decimal
    credit: Decimal
    balance: Decimal
    metadata: dict[str, Any] = {}


class FinancialReportResponse(BaseModel):
    id: str
    report_type: ReportType
    report_title: str
    from_date: date | None
    to_date: date | None
    report_date: date
    account_id: str | None
    account_code: str | None
    line_items: list[ReportLineItemResponse]
    totals: dict[str, Decimal]
    generated_at: datetime
    parameters: dict[str, Any]

    model_config = {"from_attributes": True}


class LedgerReportRequest(BaseModel):
    account_id: str
    from_date: date | None = None
    to_date: date | None = None
    save: bool = True


class TrialBalanceRequest(BaseModel):
    as_of_date: date
    save: bool = True


class IncomeStatementRequest(BaseModel):
    from_date: date
    to_date: date
    save: bool = True


class BalanceSheetRequest(BaseModel):
    as_of_date: date
    save: bool = True
