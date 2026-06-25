from datetime import datetime
from decimal import Decimal

from app.application.exceptions import ConflictError, NotFoundError, ValidationError
from app.domain.entities.voucher import LedgerEntry, Voucher, VoucherEntry
from app.domain.enums import VoucherStatus, VoucherType
from app.domain.repositories.chart_of_account_repository import ChartOfAccountRepository
from app.domain.repositories.voucher_repository import VoucherRepository


class VoucherService:
    def __init__(
        self,
        voucher_repository: VoucherRepository,
        account_repository: ChartOfAccountRepository,
    ) -> None:
        self._vouchers = voucher_repository
        self._accounts = account_repository

    async def create_voucher(self, data: dict) -> Voucher:
        voucher_type = VoucherType(data["voucher_type"])
        entries = await self._build_entries(data["entries"])
        total_debit, total_credit = self._calculate_totals(entries)
        self._validate_double_entry(entries, total_debit, total_credit)

        voucher_number = data.get("voucher_number") or await self._vouchers.get_next_voucher_number(
            voucher_type
        )
        if await self._vouchers.get_by_number(voucher_number):
            raise ConflictError(f"Voucher number '{voucher_number}' already exists")

        voucher = Voucher(
            voucher_number=voucher_number,
            voucher_type=voucher_type,
            voucher_date=data["voucher_date"],
            reference=data.get("reference"),
            narration=data.get("narration"),
            status=VoucherStatus.DRAFT,
            entries=entries,
            total_debit=total_debit,
            total_credit=total_credit,
        )
        return await self._vouchers.create(voucher)

    async def get_voucher(self, voucher_id: str) -> Voucher:
        voucher = await self._vouchers.get_by_id(voucher_id)
        if not voucher:
            raise NotFoundError("Voucher not found")
        return voucher

    async def list_vouchers(
        self,
        status: VoucherStatus | None = None,
        voucher_type: VoucherType | None = None,
        from_date=None,
        to_date=None,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[Voucher], int]:
        vouchers = await self._vouchers.list_all(status, voucher_type, from_date, to_date, skip, limit)
        total = await self._vouchers.count(status, voucher_type, from_date, to_date)
        return vouchers, total

    async def update_voucher(self, voucher_id: str, data: dict) -> Voucher:
        voucher = await self.get_voucher(voucher_id)
        if voucher.status == VoucherStatus.POSTED:
            raise ValidationError("Posted vouchers cannot be edited")
        if voucher.status == VoucherStatus.CANCELLED:
            raise ValidationError("Cancelled vouchers cannot be edited")

        if "voucher_type" in data:
            voucher.voucher_type = VoucherType(data["voucher_type"])
        if "voucher_date" in data:
            voucher.voucher_date = data["voucher_date"]
        if "reference" in data:
            voucher.reference = data["reference"]
        if "narration" in data:
            voucher.narration = data["narration"]
        if "entries" in data:
            entries = await self._build_entries(data["entries"])
            total_debit, total_credit = self._calculate_totals(entries)
            self._validate_double_entry(entries, total_debit, total_credit)
            voucher.entries = entries
            voucher.total_debit = total_debit
            voucher.total_credit = total_credit

        voucher.updated_at = datetime.utcnow()
        updated = await self._vouchers.update(voucher_id, voucher)
        if not updated:
            raise NotFoundError("Voucher not found")
        return updated

    async def cancel_voucher(self, voucher_id: str) -> Voucher:
        voucher = await self.get_voucher(voucher_id)
        if voucher.status == VoucherStatus.POSTED:
            raise ValidationError("Posted vouchers cannot be cancelled. Create a reversing entry instead.")
        if voucher.status == VoucherStatus.CANCELLED:
            raise ValidationError("Voucher is already cancelled")

        voucher.status = VoucherStatus.CANCELLED
        voucher.cancelled_at = datetime.utcnow()
        voucher.updated_at = datetime.utcnow()
        updated = await self._vouchers.update(voucher_id, voucher)
        if not updated:
            raise NotFoundError("Voucher not found")
        return updated

    async def post_voucher(self, voucher_id: str) -> Voucher:
        voucher = await self.get_voucher(voucher_id)
        if voucher.status == VoucherStatus.POSTED:
            raise ValidationError("Voucher is already posted")
        if voucher.status == VoucherStatus.CANCELLED:
            raise ValidationError("Cancelled vouchers cannot be posted")

        self._validate_double_entry(voucher.entries, voucher.total_debit, voucher.total_credit)

        ledger_entries: list[LedgerEntry] = []
        for entry in voucher.entries:
            account = await self._accounts.get_by_id(entry.account_id)
            if not account:
                raise NotFoundError(f"Account '{entry.account_code}' not found")
            if not account.is_active:
                raise ValidationError(f"Account '{entry.account_code}' is inactive")
            if account.is_group:
                raise ValidationError(f"Cannot post to group account '{entry.account_code}'")

            await self._accounts.update_balance(
                entry.account_id,
                float(entry.debit_amount),
                float(entry.credit_amount),
            )

            updated_account = await self._accounts.get_by_id(entry.account_id)
            running_balance = updated_account.current_balance if updated_account else Decimal("0.00")

            ledger_entries.append(
                LedgerEntry(
                    account_id=entry.account_id,
                    account_code=entry.account_code,
                    account_name=entry.account_name,
                    voucher_id=voucher_id,
                    voucher_number=voucher.voucher_number,
                    voucher_date=voucher.voucher_date,
                    entry_date=voucher.voucher_date,
                    description=entry.description or voucher.narration,
                    debit_amount=entry.debit_amount,
                    credit_amount=entry.credit_amount,
                    running_balance=running_balance,
                )
            )

        await self._vouchers.create_ledger_entries(ledger_entries)

        voucher.status = VoucherStatus.POSTED
        voucher.posted_at = datetime.utcnow()
        voucher.updated_at = datetime.utcnow()
        updated = await self._vouchers.update(voucher_id, voucher)
        if not updated:
            raise NotFoundError("Voucher not found")
        return updated

    async def _build_entries(self, raw_entries: list[dict]) -> list[VoucherEntry]:
        if len(raw_entries) < 2:
            raise ValidationError("A voucher must have at least two entries")

        entries: list[VoucherEntry] = []
        for index, raw in enumerate(raw_entries, start=1):
            account = await self._accounts.get_by_id(raw["account_id"])
            if not account:
                raise NotFoundError(f"Account with id '{raw['account_id']}' not found")

            debit = Decimal(str(raw.get("debit_amount", 0)))
            credit = Decimal(str(raw.get("credit_amount", 0)))
            if debit < 0 or credit < 0:
                raise ValidationError("Debit and credit amounts must be non-negative")
            if debit == 0 and credit == 0:
                raise ValidationError("Each entry must have either debit or credit amount")
            if debit > 0 and credit > 0:
                raise ValidationError("An entry cannot have both debit and credit amounts")

            entries.append(
                VoucherEntry(
                    line_number=index,
                    account_id=account.id or raw["account_id"],
                    account_code=account.code,
                    account_name=account.name,
                    description=raw.get("description"),
                    debit_amount=debit,
                    credit_amount=credit,
                )
            )
        return entries

    def _calculate_totals(self, entries: list[VoucherEntry]) -> tuple[Decimal, Decimal]:
        total_debit = sum((entry.debit_amount for entry in entries), Decimal("0.00"))
        total_credit = sum((entry.credit_amount for entry in entries), Decimal("0.00"))
        return total_debit, total_credit

    def _validate_double_entry(
        self,
        entries: list[VoucherEntry],
        total_debit: Decimal,
        total_credit: Decimal,
    ) -> None:
        if total_debit != total_credit:
            raise ValidationError(
                f"Total debit ({total_debit}) must equal total credit ({total_credit})"
            )
        if total_debit == Decimal("0.00"):
            raise ValidationError("Voucher total amount must be greater than zero")
