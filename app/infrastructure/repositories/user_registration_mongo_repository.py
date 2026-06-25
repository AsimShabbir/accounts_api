from datetime import datetime

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.domain.entities.user_registration import UserRegistration
from app.domain.repositories.user_registration_repository import UserRegistrationRepository
from app.infrastructure.repositories.mongo_utils import prepare_for_insert, serialize_document, to_object_id


class MongoUserRegistrationRepository(UserRegistrationRepository):
    def __init__(self, database: AsyncIOMotorDatabase) -> None:
        self._collection = database.user_registrations

    async def create(self, user: UserRegistration) -> UserRegistration:
        payload = prepare_for_insert(user.model_dump())
        result = await self._collection.insert_one(payload)
        created = await self._collection.find_one({"_id": result.inserted_id})
        return UserRegistration(**serialize_document(created))

    async def get_by_id(self, user_id: str) -> UserRegistration | None:
        doc = await self._collection.find_one({"_id": to_object_id(user_id)})
        return UserRegistration(**serialize_document(doc)) if doc else None

    async def get_by_email(self, email: str) -> UserRegistration | None:
        doc = await self._collection.find_one({"email": email.lower()})
        return UserRegistration(**serialize_document(doc)) if doc else None

    async def get_by_username(self, username: str) -> UserRegistration | None:
        doc = await self._collection.find_one({"username": username.lower()})
        return UserRegistration(**serialize_document(doc)) if doc else None

    async def list_all(
        self,
        is_active: bool | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[UserRegistration]:
        query: dict = {}
        if is_active is not None:
            query["is_active"] = is_active

        cursor = self._collection.find(query).sort("created_at", -1).skip(skip).limit(limit)
        return [UserRegistration(**serialize_document(doc)) async for doc in cursor]

    async def count(self, is_active: bool | None = None) -> int:
        query: dict = {}
        if is_active is not None:
            query["is_active"] = is_active
        return await self._collection.count_documents(query)
