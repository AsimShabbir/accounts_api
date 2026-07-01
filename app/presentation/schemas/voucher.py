from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator

from app.domain.enums import VoucherStatus, VoucherType


class VoucherEntryCreate(BaseModel):
    account_id: str
    description: str | None = None
    debit_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    credit_amount: Decimal = Field(default=Decimal("0.00"), ge=0)


class VoucherCreate(BaseModel):
    voucher_type: VoucherType
    voucher_date: date
    voucher_number: str | None = None
    reference: str | None = None
    narration: str | None = None
    entries: list[VoucherEntryCreate] = Field(..., min_length=2)

    @field_validator("entries")
    @classmethod
    def validate_entries(cls, value: list[VoucherEntryCreate]) -> list[VoucherEntryCreate]:
        if len(value) < 2:
            raise ValueError("At least two entries are required for double-entry bookkeeping")
        return value


class VoucherUpdate(BaseModel):
    voucher_type: VoucherType | None = None
    voucher_date: date | None = None
    reference: str | None = None
    narration: str | None = None
    entries: list[VoucherEntryCreate] | None = None


class VoucherEntryResponse(BaseModel):
    line_number: int
    account_id: str
    account_code: str
    account_name: str
    description: str | None
    debit_amount: Decimal
    credit_amount: Decimal


class VoucherResponse(BaseModel):
    id: str
    company_id: str
    voucher_number: str
    voucher_type: VoucherType
    voucher_date: date
    reference: str | None
    narration: str | None
    status: VoucherStatus
    entries: list[VoucherEntryResponse]
    total_debit: Decimal
    total_credit: Decimal
    posted_at: datetime | None
    cancelled_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
