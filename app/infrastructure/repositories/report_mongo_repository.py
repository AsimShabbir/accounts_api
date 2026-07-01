from datetime import date, datetime
from decimal import Decimal

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.domain.entities.report import FinancialReport, ReportLineItem
from app.domain.enums import ReportType
from app.domain.repositories.report_repository import ReportRepository
from app.infrastructure.repositories.mongo_utils import prepare_for_insert, serialize_document, to_object_id


class MongoReportRepository(ReportRepository):
    def __init__(self, database: AsyncIOMotorDatabase) -> None:
        self._collection = database.reports

    async def save(self, report: FinancialReport) -> FinancialReport:
        payload = prepare_for_insert(report.model_dump())
        if report.id:
            await self._collection.update_one(
                {"_id": to_object_id(report.id)},
                {"$set": payload},
            )
            doc = await self._collection.find_one({"_id": to_object_id(report.id)})
        else:
            result = await self._collection.insert_one(payload)
            doc = await self._collection.find_one({"_id": result.inserted_id})
        return FinancialReport(**self._to_entity(doc))

    async def get_by_id(self, report_id: str, company_id: str | None = None) -> FinancialReport | None:
        query: dict = {"_id": to_object_id(report_id)}
        if company_id:
            query["company_id"] = company_id
        doc = await self._collection.find_one(query)
        return FinancialReport(**self._to_entity(doc)) if doc else None

    async def list_reports(
        self,
        company_id: str,
        report_type: ReportType | None = None,
        from_date: date | None = None,
        to_date: date | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[FinancialReport]:
        query: dict = {"company_id": company_id}
        if report_type:
            query["report_type"] = report_type.value
        if from_date or to_date:
            date_filter: dict = {}
            if from_date:
                date_filter["$gte"] = datetime.combine(from_date, datetime.min.time())
            if to_date:
                date_filter["$lte"] = datetime.combine(to_date, datetime.max.time())
            query["report_date"] = date_filter

        cursor = self._collection.find(query).sort("generated_at", -1).skip(skip).limit(limit)
        return [FinancialReport(**self._to_entity(doc)) async for doc in cursor]

    def _to_entity(self, doc: dict | None) -> dict:
        data = serialize_document(doc) or {}
        if isinstance(data.get("from_date"), datetime):
            data["from_date"] = data["from_date"].date()
        if isinstance(data.get("to_date"), datetime):
            data["to_date"] = data["to_date"].date()
        if isinstance(data.get("report_date"), datetime):
            data["report_date"] = data["report_date"].date()

        line_items = []
        for item in data.get("line_items", []):
            item["debit"] = Decimal(str(item.get("debit", 0)))
            item["credit"] = Decimal(str(item.get("credit", 0)))
            item["balance"] = Decimal(str(item.get("balance", 0)))
            line_items.append(ReportLineItem(**item))
        data["line_items"] = line_items

        totals = {}
        for key, value in data.get("totals", {}).items():
            totals[key] = Decimal(str(value))
        data["totals"] = totals
        return data
