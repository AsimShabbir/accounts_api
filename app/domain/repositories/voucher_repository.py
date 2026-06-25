from abc import ABC, abstractmethod
from datetime import date

from app.domain.entities.voucher import LedgerEntry, Voucher
from app.domain.enums import VoucherStatus, VoucherType


class VoucherRepository(ABC):
    @abstractmethod
    async def create(self, voucher: Voucher) -> Voucher:
        pass

    @abstractmethod
    async def get_by_id(self, voucher_id: str) -> Voucher | None:
        pass

    @abstractmethod
    async def get_by_number(self, voucher_number: str) -> Voucher | None:
        pass

    @abstractmethod
    async def list_all(
        self,
        status: VoucherStatus | None = None,
        voucher_type: VoucherType | None = None,
        from_date: date | None = None,
        to_date: date | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Voucher]:
        pass

    @abstractmethod
    async def count(
        self,
        status: VoucherStatus | None = None,
        voucher_type: VoucherType | None = None,
        from_date: date | None = None,
        to_date: date | None = None,
    ) -> int:
        pass

    @abstractmethod
    async def update(self, voucher_id: str, voucher: Voucher) -> Voucher | None:
        pass

    @abstractmethod
    async def get_next_voucher_number(self, voucher_type: VoucherType) -> str:
        pass

    @abstractmethod
    async def create_ledger_entries(self, entries: list[LedgerEntry]) -> list[LedgerEntry]:
        pass

    @abstractmethod
    async def get_ledger_entries(
        self,
        account_id: str,
        from_date: date | None = None,
        to_date: date | None = None,
    ) -> list[LedgerEntry]:
        pass

    @abstractmethod
    async def delete_ledger_entries_by_voucher(self, voucher_id: str) -> None:
        pass
