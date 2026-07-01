from datetime import date, datetime
from decimal import Decimal

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.domain.entities.chart_of_account import ChartOfAccount
from app.domain.enums import AccountType
from app.domain.repositories.chart_of_account_repository import ChartOfAccountRepository
from app.infrastructure.repositories.mongo_utils import prepare_for_insert, serialize_document, to_object_id


class MongoChartOfAccountRepository(ChartOfAccountRepository):
    def __init__(self, database: AsyncIOMotorDatabase) -> None:
        self._collection = database.chart_of_accounts

    async def create(self, account: ChartOfAccount) -> ChartOfAccount:
        payload = prepare_for_insert(account.model_dump())
        result = await self._collection.insert_one(payload)
        created = await self._collection.find_one({"_id": result.inserted_id})
        return ChartOfAccount(**self._to_entity(created))

    async def get_by_id(self, account_id: str, company_id: str | None = None) -> ChartOfAccount | None:
        query: dict = {"_id": to_object_id(account_id)}
        if company_id:
            query["company_id"] = company_id
        doc = await self._collection.find_one(query)
        return ChartOfAccount(**self._to_entity(doc)) if doc else None

    async def get_by_code(self, company_id: str, code: str) -> ChartOfAccount | None:
        doc = await self._collection.find_one({"company_id": company_id, "code": code})
        return ChartOfAccount(**self._to_entity(doc)) if doc else None

    async def list_all(
        self,
        company_id: str,
        account_type: AccountType | None = None,
        is_active: bool | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[ChartOfAccount]:
        query: dict = {"company_id": company_id}
        if account_type:
            query["account_type"] = account_type.value
        if is_active is not None:
            query["is_active"] = is_active

        cursor = self._collection.find(query).sort("code", 1).skip(skip).limit(limit)
        return [ChartOfAccount(**self._to_entity(doc)) async for doc in cursor]

    async def count(
        self,
        company_id: str,
        account_type: AccountType | None = None,
        is_active: bool | None = None,
    ) -> int:
        query: dict = {"company_id": company_id}
        if account_type:
            query["account_type"] = account_type.value
        if is_active is not None:
            query["is_active"] = is_active
        return await self._collection.count_documents(query)

    async def update(self, account_id: str, account: ChartOfAccount) -> ChartOfAccount | None:
        payload = prepare_for_insert(account.model_dump(exclude={"id"}))
        payload["updated_at"] = datetime.utcnow()
        result = await self._collection.update_one(
            {"_id": to_object_id(account_id)},
            {"$set": payload},
        )
        if result.matched_count == 0:
            return None
        doc = await self._collection.find_one({"_id": to_object_id(account_id)})
        return ChartOfAccount(**self._to_entity(doc))

    async def delete(self, account_id: str) -> bool:
        result = await self._collection.delete_one({"_id": to_object_id(account_id)})
        return result.deleted_count > 0

    async def update_balance(self, account_id: str, debit: float, credit: float) -> None:
        doc = await self._collection.find_one({"_id": to_object_id(account_id)})
        if not doc:
            return

        nature = doc.get("nature", "debit")
        current = Decimal(str(doc.get("current_balance", 0)))
        debit_dec = Decimal(str(debit))
        credit_dec = Decimal(str(credit))

        if nature == "debit":
            new_balance = current + debit_dec - credit_dec
        else:
            new_balance = current + credit_dec - debit_dec

        await self._collection.update_one(
            {"_id": to_object_id(account_id)},
            {"$set": {"current_balance": float(new_balance), "updated_at": datetime.utcnow()}},
        )

    async def get_balances_as_of(self, company_id: str, as_of_date: date) -> list[ChartOfAccount]:
        return await self.list_all(company_id, is_active=True, skip=0, limit=10000)

    def _to_entity(self, doc: dict | None) -> dict:
        data = serialize_document(doc) or {}
        if "opening_balance" in data:
            data["opening_balance"] = Decimal(str(data["opening_balance"]))
        if "current_balance" in data:
            data["current_balance"] = Decimal(str(data["current_balance"]))
        if isinstance(data.get("voucher_date"), datetime):
            data["voucher_date"] = data["voucher_date"].date()
        return data
