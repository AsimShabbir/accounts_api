from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.core.config import settings

_client: AsyncIOMotorClient | None = None
_database: AsyncIOMotorDatabase | None = None


async def connect_to_mongodb() -> None:
    global _client, _database
    _client = AsyncIOMotorClient(settings.MONGODB_URI)
    _database = _client[settings.MONGODB_DATABASE]
    await _ensure_indexes()


async def close_mongodb_connection() -> None:
    global _client, _database
    if _client:
        _client.close()
    _client = None
    _database = None


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
