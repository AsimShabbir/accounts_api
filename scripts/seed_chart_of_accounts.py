"""Seed default chart of accounts for the accounting API."""

import asyncio
from decimal import Decimal

from app.core.database import close_mongodb_connection, connect_to_mongodb, get_database
from app.domain.entities.chart_of_account import ChartOfAccount
from app.domain.enums import AccountNature, AccountType, account_nature_for_type
from app.infrastructure.repositories.chart_of_account_mongo_repository import MongoChartOfAccountRepository

DEFAULT_ACCOUNTS = [
    {"code": "1000", "name": "Assets", "account_type": AccountType.ASSET, "is_group": True},
    {"code": "1100", "name": "Current Assets", "account_type": AccountType.ASSET, "is_group": True, "parent_code": "1000"},
    {"code": "1110", "name": "Cash", "account_type": AccountType.ASSET, "parent_code": "1100"},
    {"code": "1120", "name": "Bank Account", "account_type": AccountType.ASSET, "parent_code": "1100"},
    {"code": "1130", "name": "Accounts Receivable", "account_type": AccountType.ASSET, "parent_code": "1100"},
    {"code": "1140", "name": "Customers", "account_type": AccountType.ASSET, "is_group": True, "parent_code": "1100"},
    {"code": "1141", "name": "Acme Customer Corp", "account_type": AccountType.ASSET, "parent_code": "1140"},
    {"code": "1142", "name": "Bright Retail Ltd", "account_type": AccountType.ASSET, "parent_code": "1140"},
    {"code": "1143", "name": "City Services Co", "account_type": AccountType.ASSET, "parent_code": "1140"},
    {"code": "1144", "name": "Delta Manufacturing", "account_type": AccountType.ASSET, "parent_code": "1140"},
    {"code": "1200", "name": "Fixed Assets", "account_type": AccountType.ASSET, "is_group": True, "parent_code": "1000"},
    {"code": "1210", "name": "Equipment", "account_type": AccountType.ASSET, "parent_code": "1200"},
    {"code": "2000", "name": "Liabilities", "account_type": AccountType.LIABILITY, "is_group": True},
    {"code": "2100", "name": "Current Liabilities", "account_type": AccountType.LIABILITY, "is_group": True, "parent_code": "2000"},
    {"code": "2110", "name": "Accounts Payable", "account_type": AccountType.LIABILITY, "parent_code": "2100"},
    {"code": "2120", "name": "Accrued Expenses", "account_type": AccountType.LIABILITY, "parent_code": "2100"},
    {"code": "2130", "name": "Vendors & Suppliers", "account_type": AccountType.LIABILITY, "is_group": True, "parent_code": "2100"},
    {"code": "2131", "name": "Alpha Vendor Ltd", "account_type": AccountType.LIABILITY, "parent_code": "2130"},
    {"code": "2132", "name": "Beta Supplier Inc", "account_type": AccountType.LIABILITY, "parent_code": "2130"},
    {"code": "2133", "name": "Gamma Trading Co", "account_type": AccountType.LIABILITY, "parent_code": "2130"},
    {"code": "2134", "name": "Prime Materials Supplier", "account_type": AccountType.LIABILITY, "parent_code": "2130"},
    {"code": "3000", "name": "Equity", "account_type": AccountType.EQUITY, "is_group": True},
    {"code": "3100", "name": "Owner's Capital", "account_type": AccountType.EQUITY, "parent_code": "3000"},
    {"code": "3200", "name": "Retained Earnings", "account_type": AccountType.EQUITY, "parent_code": "3000"},
    {"code": "4000", "name": "Revenue", "account_type": AccountType.REVENUE, "is_group": True},
    {"code": "4100", "name": "Sales Revenue", "account_type": AccountType.REVENUE, "parent_code": "4000"},
    {"code": "4200", "name": "Service Revenue", "account_type": AccountType.REVENUE, "parent_code": "4000"},
    {"code": "5000", "name": "Expenses", "account_type": AccountType.EXPENSE, "is_group": True},
    {"code": "5100", "name": "Rent Expense", "account_type": AccountType.EXPENSE, "parent_code": "5000"},
    {"code": "5200", "name": "Salary Expense", "account_type": AccountType.EXPENSE, "parent_code": "5000"},
    {"code": "5300", "name": "Utilities Expense", "account_type": AccountType.EXPENSE, "parent_code": "5000"},
]


async def seed() -> None:
    await connect_to_mongodb()
    repository = MongoChartOfAccountRepository(get_database())
    code_to_id: dict[str, str] = {}

    for item in DEFAULT_ACCOUNTS:
        existing = await repository.get_by_code(item["code"])
        if existing:
            code_to_id[item["code"]] = existing.id or ""
            print(f"Skipped existing account: {item['code']}")
            continue

        parent_id = None
        level = 1
        if parent_code := item.get("parent_code"):
            parent_id = code_to_id.get(parent_code)
            if parent_id:
                parent = await repository.get_by_id(parent_id)
                level = (parent.level + 1) if parent else 2

        account_type = item["account_type"]
        account = ChartOfAccount(
            code=item["code"],
            name=item["name"],
            account_type=account_type,
            nature=account_nature_for_type(account_type),
            parent_id=parent_id,
            level=level,
            is_group=item.get("is_group", False),
            opening_balance=Decimal("0.00"),
            current_balance=Decimal("0.00"),
        )
        created = await repository.create(account)
        code_to_id[item["code"]] = created.id or ""
        print(f"Created account: {item['code']} - {item['name']}")

    await close_mongodb_connection()
    print("Seed completed.")


if __name__ == "__main__":
    asyncio.run(seed())
