from datetime import date, datetime
from decimal import Decimal

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.domain.entities.voucher import LedgerEntry, Voucher, VoucherEntry
from app.domain.enums import VoucherStatus, VoucherType
from app.domain.repositories.voucher_repository import VoucherRepository
from app.infrastructure.repositories.mongo_utils import prepare_for_insert, serialize_document, to_object_id

VOUCHER_PREFIX = {
    VoucherType.JOURNAL: "JV",
    VoucherType.PAYMENT: "PV",
    VoucherType.RECEIPT: "RV",
    VoucherType.CONTRA: "CV",
    VoucherType.SALES: "SV",
    VoucherType.PURCHASE: "PU",
}


class MongoVoucherRepository(VoucherRepository):
    def __init__(self, database: AsyncIOMotorDatabase) -> None:
        self._vouchers = database.vouchers
        self._ledger = database.ledger_entries

    async def create(self, voucher: Voucher) -> Voucher:
        payload = prepare_for_insert(voucher.model_dump())
        result = await self._vouchers.insert_one(payload)
        created = await self._vouchers.find_one({"_id": result.inserted_id})
        return Voucher(**self._to_voucher_entity(created))

    async def get_by_id(self, voucher_id: str) -> Voucher | None:
        doc = await self._vouchers.find_one({"_id": to_object_id(voucher_id)})
        return Voucher(**self._to_voucher_entity(doc)) if doc else None

    async def get_by_number(self, voucher_number: str) -> Voucher | None:
        doc = await self._vouchers.find_one({"voucher_number": voucher_number})
        return Voucher(**self._to_voucher_entity(doc)) if doc else None

    async def list_all(
        self,
        status: VoucherStatus | None = None,
        voucher_type: VoucherType | None = None,
        from_date: date | None = None,
        to_date: date | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Voucher]:
        query = self._build_query(status, voucher_type, from_date, to_date)
        cursor = self._vouchers.find(query).sort("voucher_date", -1).skip(skip).limit(limit)
        return [Voucher(**self._to_voucher_entity(doc)) async for doc in cursor]

    async def count(
        self,
        status: VoucherStatus | None = None,
        voucher_type: VoucherType | None = None,
        from_date: date | None = None,
        to_date: date | None = None,
    ) -> int:
        query = self._build_query(status, voucher_type, from_date, to_date)
        return await self._vouchers.count_documents(query)

    async def update(self, voucher_id: str, voucher: Voucher) -> Voucher | None:
        payload = prepare_for_insert(voucher.model_dump(exclude={"id"}))
        payload["updated_at"] = datetime.utcnow()
        result = await self._vouchers.update_one(
            {"_id": to_object_id(voucher_id)},
            {"$set": payload},
        )
        if result.matched_count == 0:
            return None
        doc = await self._vouchers.find_one({"_id": to_object_id(voucher_id)})
        return Voucher(**self._to_voucher_entity(doc))

    async def get_next_voucher_number(self, voucher_type: VoucherType) -> str:
        prefix = VOUCHER_PREFIX[voucher_type]
        year = datetime.utcnow().year
        pattern = f"^{prefix}-{year}-"
        latest = await self._vouchers.find_one(
            {"voucher_number": {"$regex": pattern}},
            sort=[("voucher_number", -1)],
        )
        if not latest:
            return f"{prefix}-{year}-0001"

        last_number = int(latest["voucher_number"].split("-")[-1])
        return f"{prefix}-{year}-{last_number + 1:04d}"

    async def create_ledger_entries(self, entries: list[LedgerEntry]) -> list[LedgerEntry]:
        if not entries:
            return []
        payloads = [prepare_for_insert(entry.model_dump()) for entry in entries]
        result = await self._ledger.insert_many(payloads)
        created: list[LedgerEntry] = []
        for inserted_id in result.inserted_ids:
            doc = await self._ledger.find_one({"_id": inserted_id})
            created.append(LedgerEntry(**self._to_ledger_entity(doc)))
        return created

    async def get_ledger_entries(
        self,
        account_id: str,
        from_date: date | None = None,
        to_date: date | None = None,
    ) -> list[LedgerEntry]:
        query: dict = {"account_id": account_id}
        if from_date or to_date:
            date_filter: dict = {}
            if from_date:
                date_filter["$gte"] = datetime.combine(from_date, datetime.min.time())
            if to_date:
                date_filter["$lte"] = datetime.combine(to_date, datetime.max.time())
            query["entry_date"] = date_filter

        cursor = self._ledger.find(query).sort([("entry_date", 1), ("created_at", 1)])
        return [LedgerEntry(**self._to_ledger_entity(doc)) async for doc in cursor]

    async def delete_ledger_entries_by_voucher(self, voucher_id: str) -> None:
        await self._ledger.delete_many({"voucher_id": voucher_id})

    def _build_query(
        self,
        status: VoucherStatus | None,
        voucher_type: VoucherType | None,
        from_date: date | None,
        to_date: date | None,
    ) -> dict:
        query: dict = {}
        if status:
            query["status"] = status.value
        if voucher_type:
            query["voucher_type"] = voucher_type.value
        if from_date or to_date:
            date_filter: dict = {}
            if from_date:
                date_filter["$gte"] = datetime.combine(from_date, datetime.min.time())
            if to_date:
                date_filter["$lte"] = datetime.combine(to_date, datetime.max.time())
            query["voucher_date"] = date_filter
        return query

    def _to_voucher_entity(self, doc: dict | None) -> dict:
        data = serialize_document(doc) or {}
        data["total_debit"] = Decimal(str(data.get("total_debit", 0)))
        data["total_credit"] = Decimal(str(data.get("total_credit", 0)))
        if isinstance(data.get("voucher_date"), datetime):
            data["voucher_date"] = data["voucher_date"].date()

        entries = []
        for entry in data.get("entries", []):
            entry["debit_amount"] = Decimal(str(entry.get("debit_amount", 0)))
            entry["credit_amount"] = Decimal(str(entry.get("credit_amount", 0)))
            entries.append(entry)
        data["entries"] = entries
        return data

    def _to_ledger_entity(self, doc: dict | None) -> dict:
        data = serialize_document(doc) or {}
        data["debit_amount"] = Decimal(str(data.get("debit_amount", 0)))
        data["credit_amount"] = Decimal(str(data.get("credit_amount", 0)))
        data["running_balance"] = Decimal(str(data.get("running_balance", 0)))
        if isinstance(data.get("entry_date"), datetime):
            data["entry_date"] = data["entry_date"].date()
        if isinstance(data.get("voucher_date"), datetime):
            data["voucher_date"] = data["voucher_date"].date()
        return data
