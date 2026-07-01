"""Seed AHSoftech and Beela companies for the first active user."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.create_company_assets import main as create_assets

from app.core.database import close_mongodb_connection, connect_to_mongodb, get_database
from app.domain.entities.company import Company
from app.infrastructure.repositories.company_mongo_repository import MongoCompanyRepository
from app.infrastructure.repositories.user_registration_mongo_repository import MongoUserRegistrationRepository

DEFAULT_COMPANIES = [
    {
        "company_id": "ahsoftech",
        "name": "AHSoftech",
        "address": "123 Tech Park, Silicon Valley, CA 94025, USA",
        "logo": "/static/companies/ahsoftech/logo.png",
        "favicon": "/static/companies/ahsoftech/favicon.png",
    },
    {
        "company_id": "beela",
        "name": "Beela",
        "address": "45 Commerce Street, Karachi, Pakistan",
        "logo": "/static/companies/beela/logo.png",
        "favicon": "/static/companies/beela/favicon.png",
    },
]


async def seed(user_email: str | None = None) -> None:
    create_assets()

    await connect_to_mongodb()
    db = get_database()
    user_repo = MongoUserRegistrationRepository(db)
    company_repo = MongoCompanyRepository(db)

    if user_email:
        user = await user_repo.get_by_email(user_email)
        if not user:
            print(f"No user found with email: {user_email}")
            await close_mongodb_connection()
            return
    else:
        users = await user_repo.list_all(is_active=True, limit=1)
        if not users:
            print("No active users found. Register a user first, then run this seed.")
            await close_mongodb_connection()
            return
        user = users[0]

    user_id = user.id or ""
    print(f"Seeding companies for user: {user.username} ({user.email})")

    for item in DEFAULT_COMPANIES:
        existing = await company_repo.get_by_company_id(item["company_id"], user_id)
        if existing:
            print(f"Skipped existing company: {item['name']}")
            continue

        company = Company(
            company_id=item["company_id"],
            name=item["name"],
            address=item["address"],
            logo=item["logo"],
            favicon=item["favicon"],
            user_id=user_id,
        )
        created = await company_repo.create(company)
        print(f"Created company: {created.name} (id={created.id})")

    await close_mongodb_connection()
    print("Company seed completed.")


if __name__ == "__main__":
    email = sys.argv[1] if len(sys.argv) > 1 else None
    asyncio.run(seed(email))
