# Accounting API

FastAPI-based double-entry accounting system with Clean Architecture and MongoDB.

## Features

- **Chart of Accounts** — hierarchical accounts (Asset, Liability, Equity, Revenue, Expense)
- **Double-Entry Vouchers** — Journal, Payment, Receipt, Contra, Sales, Purchase
- **Voucher Lifecycle** — Create (draft), Edit, Cancel, Post (posted vouchers are locked)
- **Financial Reports** — Ledger, Trial Balance, Income Statement, Balance Sheet
- **DataTable API** — paginated list endpoints for accounts and vouchers
- **Report Persistence** — generated reports saved to MongoDB

## Architecture

```
app/
├── core/           # Config, database connection
├── domain/         # Entities, enums, repository interfaces
├── application/    # Business logic services
├── infrastructure/ # MongoDB repository implementations
└── presentation/   # FastAPI routes, schemas, dependencies
```

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and set your MongoDB credentials (already configured in `.env`).

Seed default chart of accounts:

```bash
python scripts/seed_chart_of_accounts.py
```

Run the API:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API docs: http://localhost:8000/docs

## API Endpoints

### Chart of Accounts (`/api/v1/chart-of-accounts`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/` | Create account |
| GET | `/` | List accounts (DataTable) |
| GET | `/{id}` | Get account |
| PUT | `/{id}` | Update account |
| DELETE | `/{id}` | Delete account |

### Vouchers (`/api/v1/vouchers`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/` | Create draft voucher |
| GET | `/` | List vouchers (DataTable) |
| GET | `/{id}` | Get voucher |
| PUT | `/{id}` | Edit draft voucher |
| POST | `/{id}/cancel` | Cancel draft voucher |
| POST | `/{id}/post` | Post voucher (updates balances) |

### Reports (`/api/v1/reports`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/ledger` | Account ledger for date range |
| POST | `/trial-balance` | Trial balance as of date |
| POST | `/income-statement` | P&L for date range |
| POST | `/balance-sheet` | Balance sheet as of date |
| GET | `/` | List saved reports |
| GET | `/{id}` | Get saved report |

## Example: Create and Post a Journal Voucher

```json
POST /api/v1/vouchers
{
  "voucher_type": "journal",
  "voucher_date": "2025-06-01",
  "narration": "Initial capital injection",
  "entries": [
    {"account_id": "<cash_account_id>", "debit_amount": 10000, "credit_amount": 0},
    {"account_id": "<capital_account_id>", "debit_amount": 0, "credit_amount": 10000}
  ]
}
```

Then post: `POST /api/v1/vouchers/{id}/post`

## MongoDB Collections

- `chart_of_accounts` — Chart of accounts
- `vouchers` — Voucher headers and entries
- `ledger_entries` — Posted transaction lines
- `reports` — Generated financial reports
