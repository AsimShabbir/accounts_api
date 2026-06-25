from enum import Enum


class AccountType(str, Enum):
    ASSET = "asset"
    LIABILITY = "liability"
    EQUITY = "equity"
    REVENUE = "revenue"
    EXPENSE = "expense"


class AccountNature(str, Enum):
    DEBIT = "debit"
    CREDIT = "credit"


class VoucherType(str, Enum):
    JOURNAL = "journal"
    PAYMENT = "payment"
    RECEIPT = "receipt"
    CONTRA = "contra"
    SALES = "sales"
    PURCHASE = "purchase"


class VoucherStatus(str, Enum):
    DRAFT = "draft"
    POSTED = "posted"
    CANCELLED = "cancelled"


class ReportType(str, Enum):
    LEDGER = "ledger"
    TRIAL_BALANCE = "trial_balance"
    INCOME_STATEMENT = "income_statement"
    BALANCE_SHEET = "balance_sheet"


def account_nature_for_type(account_type: AccountType) -> AccountNature:
    if account_type in (AccountType.ASSET, AccountType.EXPENSE):
        return AccountNature.DEBIT
    return AccountNature.CREDIT
