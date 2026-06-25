from datetime import datetime
from decimal import Decimal

from app.application.exceptions import ConflictError, NotFoundError, ValidationError
from app.domain.entities.chart_of_account import ChartOfAccount
from app.domain.enums import AccountNature, AccountType, account_nature_for_type
from app.domain.repositories.chart_of_account_repository import ChartOfAccountRepository


class ChartOfAccountService:
    def __init__(self, repository: ChartOfAccountRepository) -> None:
        self._repository = repository

    async def create_account(self, data: dict) -> ChartOfAccount:
        existing = await self._repository.get_by_code(data["code"])
        if existing:
            raise ConflictError(f"Account code '{data['code']}' already exists")

        account_type = AccountType(data["account_type"])
        nature = AccountNature(data.get("nature") or account_nature_for_type(account_type).value)

        if data.get("parent_id"):
            parent = await self._repository.get_by_id(data["parent_id"])
            if not parent:
                raise NotFoundError("Parent account not found")
            if not parent.is_group:
                raise ValidationError("Parent account must be a group account")
            level = parent.level + 1
        else:
            level = 1

        opening_balance = Decimal(str(data.get("opening_balance", 0)))
        account = ChartOfAccount(
            code=data["code"],
            name=data["name"],
            account_type=account_type,
            nature=nature,
            parent_id=data.get("parent_id"),
            level=level,
            is_group=data.get("is_group", False),
            is_active=data.get("is_active", True),
            opening_balance=opening_balance,
            current_balance=opening_balance,
            description=data.get("description"),
        )
        return await self._repository.create(account)

    async def get_account(self, account_id: str) -> ChartOfAccount:
        account = await self._repository.get_by_id(account_id)
        if not account:
            raise NotFoundError("Account not found")
        return account

    async def list_accounts(
        self,
        account_type: AccountType | None = None,
        is_active: bool | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[ChartOfAccount], int]:
        accounts = await self._repository.list_all(account_type, is_active, skip, limit)
        total = await self._repository.count(account_type, is_active)
        return accounts, total

    async def update_account(self, account_id: str, data: dict) -> ChartOfAccount:
        account = await self.get_account(account_id)

        if "code" in data and data["code"] != account.code:
            existing = await self._repository.get_by_code(data["code"])
            if existing:
                raise ConflictError(f"Account code '{data['code']}' already exists")
            account.code = data["code"]

        if "name" in data:
            account.name = data["name"]
        if "account_type" in data:
            account.account_type = AccountType(data["account_type"])
            account.nature = account_nature_for_type(account.account_type)
        if "parent_id" in data:
            account.parent_id = data["parent_id"]
        if "is_group" in data:
            account.is_group = data["is_group"]
        if "is_active" in data:
            account.is_active = data["is_active"]
        if "description" in data:
            account.description = data["description"]
        if "opening_balance" in data:
            diff = Decimal(str(data["opening_balance"])) - account.opening_balance
            account.opening_balance = Decimal(str(data["opening_balance"]))
            account.current_balance += diff

        account.updated_at = datetime.utcnow()
        updated = await self._repository.update(account_id, account)
        if not updated:
            raise NotFoundError("Account not found")
        return updated

    async def delete_account(self, account_id: str) -> None:
        account = await self.get_account(account_id)
        if account.current_balance != Decimal("0.00"):
            raise ValidationError("Cannot delete account with non-zero balance")
        deleted = await self._repository.delete(account_id)
        if not deleted:
            raise NotFoundError("Account not found")

