from datetime import date
from decimal import Decimal

from app.application.exceptions import NotFoundError, ValidationError
from app.domain.entities.report import FinancialReport, ReportLineItem
from app.domain.enums import AccountNature, AccountType, ReportType
from app.domain.repositories.chart_of_account_repository import ChartOfAccountRepository
from app.domain.repositories.report_repository import ReportRepository
from app.domain.repositories.voucher_repository import VoucherRepository


class ReportService:
    def __init__(
        self,
        account_repository: ChartOfAccountRepository,
        voucher_repository: VoucherRepository,
        report_repository: ReportRepository,
    ) -> None:
        self._accounts = account_repository
        self._vouchers = voucher_repository
        self._reports = report_repository

    async def generate_ledger(
        self,
        account_id: str,
        from_date: date | None = None,
        to_date: date | None = None,
        save: bool = True,
    ) -> FinancialReport:
        account = await self._accounts.get_by_id(account_id)
        if not account:
            raise NotFoundError("Account not found")

        entries = await self._vouchers.get_ledger_entries(account_id, from_date, to_date)
        line_items = [
            ReportLineItem(
                account_id=account_id,
                account_code=entry.account_code,
                account_name=entry.account_name,
                debit=entry.debit_amount,
                credit=entry.credit_amount,
                balance=entry.running_balance,
                metadata={
                    "voucher_id": entry.voucher_id,
                    "voucher_number": entry.voucher_number,
                    "voucher_date": str(entry.voucher_date),
                    "description": entry.description,
                },
            )
            for entry in entries
        ]

        total_debit = sum((item.debit for item in line_items), Decimal("0.00"))
        total_credit = sum((item.credit for item in line_items), Decimal("0.00"))
        closing_balance = entries[-1].running_balance if entries else account.current_balance

        report = FinancialReport(
            report_type=ReportType.LEDGER,
            report_title=f"Ledger - {account.code} {account.name}",
            from_date=from_date,
            to_date=to_date,
            report_date=to_date or date.today(),
            account_id=account_id,
            account_code=account.code,
            line_items=line_items,
            totals={
                "total_debit": total_debit,
                "total_credit": total_credit,
                "closing_balance": closing_balance,
            },
            parameters={"account_id": account_id},
        )
        return await self._reports.save(report) if save else report

    async def generate_trial_balance(
        self,
        as_of_date: date,
        save: bool = True,
    ) -> FinancialReport:
        accounts = await self._accounts.list_all(is_active=True, skip=0, limit=10000)
        line_items: list[ReportLineItem] = []
        total_debit = Decimal("0.00")
        total_credit = Decimal("0.00")

        for account in accounts:
            if account.is_group:
                continue

            balance = await self._get_account_balance_as_of(account.id or "", as_of_date, account)
            if balance == Decimal("0.00"):
                continue

            if account.nature == AccountNature.DEBIT:
                debit = balance if balance > 0 else Decimal("0.00")
                credit = abs(balance) if balance < 0 else Decimal("0.00")
            else:
                credit = balance if balance > 0 else Decimal("0.00")
                debit = abs(balance) if balance < 0 else Decimal("0.00")

            line_items.append(
                ReportLineItem(
                    account_id=account.id,
                    account_code=account.code,
                    account_name=account.name,
                    account_type=account.account_type.value,
                    debit=debit,
                    credit=credit,
                    balance=balance,
                )
            )
            total_debit += debit
            total_credit += credit

        report = FinancialReport(
            report_type=ReportType.TRIAL_BALANCE,
            report_title="Trial Balance",
            report_date=as_of_date,
            line_items=sorted(line_items, key=lambda item: item.account_code),
            totals={
                "total_debit": total_debit,
                "total_credit": total_credit,
                "difference": total_debit - total_credit,
            },
            parameters={"as_of_date": str(as_of_date)},
        )
        return await self._reports.save(report) if save else report

    async def generate_income_statement(
        self,
        from_date: date,
        to_date: date,
        save: bool = True,
    ) -> FinancialReport:
        if from_date > to_date:
            raise ValidationError("from_date cannot be after to_date")

        accounts = await self._accounts.list_all(is_active=True, skip=0, limit=10000)
        revenue_items: list[ReportLineItem] = []
        expense_items: list[ReportLineItem] = []
        total_revenue = Decimal("0.00")
        total_expense = Decimal("0.00")

        for account in accounts:
            if account.is_group:
                continue

            if account.account_type == AccountType.REVENUE:
                amount = await self._get_period_movement(account.id or "", from_date, to_date, account)
                if amount != Decimal("0.00"):
                    revenue_items.append(
                        ReportLineItem(
                            account_id=account.id,
                            account_code=account.code,
                            account_name=account.name,
                            account_type=account.account_type.value,
                            balance=amount,
                        )
                    )
                    total_revenue += amount
            elif account.account_type == AccountType.EXPENSE:
                amount = await self._get_period_movement(account.id or "", from_date, to_date, account)
                if amount != Decimal("0.00"):
                    expense_items.append(
                        ReportLineItem(
                            account_id=account.id,
                            account_code=account.code,
                            account_name=account.name,
                            account_type=account.account_type.value,
                            balance=amount,
                        )
                    )
                    total_expense += amount

        net_income = total_revenue - total_expense
        line_items = sorted(revenue_items, key=lambda item: item.account_code) + sorted(
            expense_items, key=lambda item: item.account_code
        )

        report = FinancialReport(
            report_type=ReportType.INCOME_STATEMENT,
            report_title="Income Statement",
            from_date=from_date,
            to_date=to_date,
            report_date=to_date,
            line_items=line_items,
            totals={
                "total_revenue": total_revenue,
                "total_expense": total_expense,
                "net_income": net_income,
            },
            parameters={"from_date": str(from_date), "to_date": str(to_date)},
        )
        return await self._reports.save(report) if save else report

    async def generate_balance_sheet(
        self,
        as_of_date: date,
        save: bool = True,
    ) -> FinancialReport:
        accounts = await self._accounts.list_all(is_active=True, skip=0, limit=10000)
        assets: list[ReportLineItem] = []
        liabilities: list[ReportLineItem] = []
        equity: list[ReportLineItem] = []
        total_assets = Decimal("0.00")
        total_liabilities = Decimal("0.00")
        total_equity = Decimal("0.00")

        for account in accounts:
            if account.is_group:
                continue

            balance = await self._get_account_balance_as_of(account.id or "", as_of_date, account)
            if balance == Decimal("0.00"):
                continue

            item = ReportLineItem(
                account_id=account.id,
                account_code=account.code,
                account_name=account.name,
                account_type=account.account_type.value,
                balance=balance,
            )

            if account.account_type == AccountType.ASSET:
                assets.append(item)
                total_assets += balance
            elif account.account_type == AccountType.LIABILITY:
                liabilities.append(item)
                total_liabilities += balance
            elif account.account_type == AccountType.EQUITY:
                equity.append(item)
                total_equity += balance

        line_items = (
            sorted(assets, key=lambda item: item.account_code)
            + sorted(liabilities, key=lambda item: item.account_code)
            + sorted(equity, key=lambda item: item.account_code)
        )

        report = FinancialReport(
            report_type=ReportType.BALANCE_SHEET,
            report_title="Balance Sheet",
            report_date=as_of_date,
            line_items=line_items,
            totals={
                "total_assets": total_assets,
                "total_liabilities": total_liabilities,
                "total_equity": total_equity,
                "liabilities_and_equity": total_liabilities + total_equity,
            },
            parameters={"as_of_date": str(as_of_date)},
        )
        return await self._reports.save(report) if save else report

    async def get_report(self, report_id: str) -> FinancialReport:
        report = await self._reports.get_by_id(report_id)
        if not report:
            raise NotFoundError("Report not found")
        return report

    async def list_reports(
        self,
        report_type: ReportType | None = None,
        from_date: date | None = None,
        to_date: date | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[FinancialReport]:
        return await self._reports.list_reports(report_type, from_date, to_date, skip, limit)

    async def _get_account_balance_as_of(self, account_id: str, as_of_date: date, account) -> Decimal:
        entries = await self._vouchers.get_ledger_entries(account_id, None, as_of_date)
        if entries:
            return entries[-1].running_balance
        return account.opening_balance

    async def _get_period_movement(
        self,
        account_id: str,
        from_date: date,
        to_date: date,
        account,
    ) -> Decimal:
        entries = await self._vouchers.get_ledger_entries(account_id, from_date, to_date)
        if not entries:
            return Decimal("0.00")

        movement = Decimal("0.00")
        for entry in entries:
            if account.nature == AccountNature.DEBIT:
                movement += entry.debit_amount - entry.credit_amount
            else:
                movement += entry.credit_amount - entry.debit_amount
        return movement
