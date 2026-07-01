from datetime import datetime

from motor.motor_asyncio import AsyncIOMotorDatabase

from bson import ObjectId

from app.domain.entities.company import Company
from app.domain.repositories.company_repository import CompanyRepository
from app.infrastructure.repositories.mongo_utils import prepare_for_insert, serialize_document, to_object_id


class MongoCompanyRepository(CompanyRepository):
    def __init__(self, database: AsyncIOMotorDatabase) -> None:
        self._collection = database.companies

    async def create(self, company: Company) -> Company:
        payload = prepare_for_insert(company.model_dump())
        result = await self._collection.insert_one(payload)
        created = await self._collection.find_one({"_id": result.inserted_id})
        return Company(**serialize_document(created))

    async def get_by_id(self, company_id: str) -> Company | None:
        doc = await self._collection.find_one({"_id": to_object_id(company_id)})
        return Company(**serialize_document(doc)) if doc else None

    async def get_by_company_id(self, company_id: str, user_id: str) -> Company | None:
        doc = await self._collection.find_one({"company_id": company_id, "user_id": user_id})
        return Company(**serialize_document(doc)) if doc else None

    async def get_for_user(self, company_key: str, user_id: str) -> Company | None:
        company = await self.get_by_company_id(company_key, user_id)
        if company:
            return company
        if ObjectId.is_valid(company_key):
            company = await self.get_by_id(company_key)
            if company and company.user_id == user_id:
                return company
        return None

    async def list_by_user(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Company]:
        cursor = (
            self._collection.find({"user_id": user_id})
            .sort("name", 1)
            .skip(skip)
            .limit(limit)
        )
        return [Company(**serialize_document(doc)) async for doc in cursor]

    async def count_by_user(self, user_id: str) -> int:
        return await self._collection.count_documents({"user_id": user_id})

    async def update(self, company_id: str, company: Company) -> Company | None:
        payload = prepare_for_insert(company.model_dump(exclude={"id"}))
        payload["updated_at"] = datetime.utcnow()
        result = await self._collection.update_one(
            {"_id": to_object_id(company_id)},
            {"$set": payload},
        )
        if result.matched_count == 0:
            return None
        doc = await self._collection.find_one({"_id": to_object_id(company_id)})
        return Company(**serialize_document(doc))

    async def delete(self, company_id: str) -> bool:
        result = await self._collection.delete_one({"_id": to_object_id(company_id)})
        return result.deleted_count > 0
