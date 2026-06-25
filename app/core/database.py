import os

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.core.config import settings

_client: AsyncIOMotorClient | None = None
_database: AsyncIOMotorDatabase | None = None
_indexes_ensured: bool = False


async def ensure_connected() -> AsyncIOMotorDatabase:
    global _client, _database, _indexes_ensured

    if not settings.MONGODB_URI:
        raise RuntimeError("MONGODB_URI environment variable is not set")

    if _database is None:
        _client = AsyncIOMotorClient(
            settings.MONGODB_URI,
            serverSelectionTimeoutMS=10000,
            connectTimeoutMS=10000,
        )
        _database = _client[settings.MONGODB_DATABASE]

    if not _indexes_ensured:
        await _ensure_indexes()
        _indexes_ensured = True

    return _database


async def connect_to_mongodb() -> None:
    await ensure_connected()


async def close_mongodb_connection() -> None:
    global _client, _database, _indexes_ensured
    if _client:
        _client.close()
    _client = None
    _database = None
    _indexes_ensured = False


def get_database() -> AsyncIOMotorDatabase:
    if _database is None:
        raise RuntimeError("Database is not initialized")
    return _database


async def _ensure_indexes() -> None:
    db = get_database()

    await db.chart_of_accounts.create_index("code", unique=True)
    await db.chart_of_accounts.create_index("account_type")
    await db.chart_of_accounts.create_index("parent_id")

    await db.vouchers.create_index("voucher_number", unique=True)
    await db.vouchers.create_index("voucher_date")
    await db.vouchers.create_index("status")
    await db.vouchers.create_index([("entries.account_id", 1)])

    await db.ledger_entries.create_index([("account_id", 1), ("entry_date", 1)])
    await db.ledger_entries.create_index("voucher_id")

    await db.reports.create_index([("report_type", 1), ("generated_at", -1)])
    await db.reports.create_index("report_date")

    await db.user_registrations.create_index("email", unique=True)
    await db.user_registrations.create_index("username", unique=True)
    await db.user_registrations.create_index("is_active")

    await db.refresh_tokens.create_index("jti", unique=True)
    await db.refresh_tokens.create_index("user_id")
    await db.refresh_tokens.create_index("expires_at")
