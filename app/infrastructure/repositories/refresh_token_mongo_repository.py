from datetime import datetime

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.domain.entities.refresh_token import RefreshToken
from app.domain.repositories.refresh_token_repository import RefreshTokenRepository
from app.infrastructure.repositories.mongo_utils import prepare_for_insert, serialize_document


class MongoRefreshTokenRepository(RefreshTokenRepository):
    def __init__(self, database: AsyncIOMotorDatabase) -> None:
        self._collection = database.refresh_tokens

    async def create(self, token: RefreshToken) -> RefreshToken:
        payload = prepare_for_insert(token.model_dump())
        result = await self._collection.insert_one(payload)
        created = await self._collection.find_one({"_id": result.inserted_id})
        return RefreshToken(**self._to_entity(created))

    async def get_by_jti(self, jti: str) -> RefreshToken | None:
        doc = await self._collection.find_one({"jti": jti, "is_revoked": False})
        return RefreshToken(**self._to_entity(doc)) if doc else None

    async def revoke(self, jti: str) -> None:
        await self._collection.update_one(
            {"jti": jti},
            {"$set": {"is_revoked": True}},
        )

    def _to_entity(self, doc: dict | None) -> dict:
        data = serialize_document(doc) or {}
        if isinstance(data.get("expires_at"), datetime):
            pass
        return data
