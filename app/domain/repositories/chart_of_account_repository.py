from abc import ABC, abstractmethod
from datetime import date

from app.domain.entities.chart_of_account import ChartOfAccount
from app.domain.enums import AccountType


class ChartOfAccountRepository(ABC):
    @abstractmethod
    async def create(self, account: ChartOfAccount) -> ChartOfAccount:
        pass

    @abstractmethod
    async def get_by_id(self, account_id: str, company_id: str | None = None) -> ChartOfAccount | None:
        pass

    @abstractmethod
    async def get_by_code(self, company_id: str, code: str) -> ChartOfAccount | None:
        pass

    @abstractmethod
    async def list_all(
        self,
        company_id: str,
        account_type: AccountType | None = None,
        is_active: bool | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[ChartOfAccount]:
        pass

    @abstractmethod
    async def count(
        self,
        company_id: str,
        account_type: AccountType | None = None,
        is_active: bool | None = None,
    ) -> int:
        pass

    @abstractmethod
    async def update(self, account_id: str, account: ChartOfAccount) -> ChartOfAccount | None:
        pass

    @abstractmethod
    async def delete(self, account_id: str) -> bool:
        pass

    @abstractmethod
    async def update_balance(self, account_id: str, debit: float, credit: float) -> None:
        pass

    @abstractmethod
    async def get_balances_as_of(self, company_id: str, as_of_date: date) -> list[ChartOfAccount]:
        pass
