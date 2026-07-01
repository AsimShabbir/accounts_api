from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.domain.enums import VoucherStatus, VoucherType


class VoucherEntry(BaseModel):
    line_number: int
    account_id: str
    account_code: str
    account_name: str
    description: str | None = None
    debit_amount: Decimal = Field(default=Decimal("0.00"), decimal_places=2)
    credit_amount: Decimal = Field(default=Decimal("0.00"), decimal_places=2)


class Voucher(BaseModel):
    id: str | None = None
    company_id: str
    voucher_number: str
    voucher_type: VoucherType
    voucher_date: date
    reference: str | None = None
    narration: str | None = None
    status: VoucherStatus = VoucherStatus.DRAFT
    entries: list[VoucherEntry] = Field(default_factory=list)
    total_debit: Decimal = Field(default=Decimal("0.00"), decimal_places=2)
    total_credit: Decimal = Field(default=Decimal("0.00"), decimal_places=2)
    posted_at: datetime | None = None
    cancelled_at: datetime | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"from_attributes": True}


class LedgerEntry(BaseModel):
    id: str | None = None
    company_id: str
    account_id: str
    account_code: str
    account_name: str
    voucher_id: str
    voucher_number: str
    voucher_date: date
    entry_date: date
    description: str | None = None
    debit_amount: Decimal = Field(default=Decimal("0.00"), decimal_places=2)
    credit_amount: Decimal = Field(default=Decimal("0.00"), decimal_places=2)
    running_balance: Decimal = Field(default=Decimal("0.00"), decimal_places=2)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"from_attributes": True}
