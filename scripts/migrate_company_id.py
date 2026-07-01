"""Backfill company_id on chart_of_accounts, vouchers, ledger_entries, and reports."""

import asyncio
import sys
from pathlib import Path

from bson import ObjectId

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.database import close_mongodb_connection, connect_to_mongodb, get_database

COLLECTIONS = ("chart_of_accounts", "vouchers", "ledger_entries", "reports")


async def migrate(default_company_id: str | None = None) -> None:
    await connect_to_mongodb()
    db = get_database()

    if default_company_id:
        company = await db.companies.find_one({"_id": ObjectId(default_company_id)})
        if not company:
            print(f"Company not found: {default_company_id}")
            await close_mongodb_connection()
            return
        company_oid = str(company["_id"])
        company_name = company.get("name", "")
    else:
        company = await db.companies.find_one({}, sort=[("created_at", 1)])
        if not company:
            print("No companies found. Run scripts/seed_companies.py first.")
            await close_mongodb_connection()
            return
        company_oid = str(company["_id"])
        company_name = company.get("name", "")

    print(f"Using default company: {company_name} (id={company_oid})")

    filter_missing = {
        "$or": [
            {"company_id": {"$exists": False}},
            {"company_id": None},
            {"company_id": ""},
        ]
    }

    for coll_name in COLLECTIONS:
        result = await db[coll_name].update_many(
            filter_missing,
            {"$set": {"company_id": company_oid}},
        )
        print(f"Updated {result.modified_count} documents in '{coll_name}'")

    existing_coa_indexes = await db.chart_of_accounts.index_information()
    if "code_1" in existing_coa_indexes:
        await db.chart_of_accounts.drop_index("code_1")
        print("Dropped legacy chart_of_accounts index: code_1")

    await close_mongodb_connection()
    print("Migration completed.")


if __name__ == "__main__":
    company_id = sys.argv[1] if len(sys.argv) > 1 else None
    asyncio.run(migrate(company_id))
