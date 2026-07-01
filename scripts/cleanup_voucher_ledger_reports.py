"""Remove all voucher, ledger, and report documents from MongoDB."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.database import close_mongodb_connection, connect_to_mongodb, get_database

COLLECTIONS = ("vouchers", "ledger_entries", "reports")


async def cleanup() -> None:
    await connect_to_mongodb()
    db = get_database()

    for name in COLLECTIONS:
        result = await db[name].delete_many({})
        print(f"Deleted {result.deleted_count} documents from '{name}'")

    await close_mongodb_connection()
    print("Cleanup completed.")


if __name__ == "__main__":
    asyncio.run(cleanup())
