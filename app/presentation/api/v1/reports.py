from datetime import date

from fastapi import APIRouter, Depends, Query

from app.application.services.report_service import ReportService
from app.domain.enums import ReportType
from app.presentation.dependencies import get_report_service
from app.presentation.mappers import to_report_response
from app.presentation.schemas.report import (
    BalanceSheetRequest,
    FinancialReportResponse,
    IncomeStatementRequest,
    LedgerReportRequest,
    TrialBalanceRequest,
)

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.post("/ledger", response_model=FinancialReportResponse)
async def generate_ledger(
    payload: LedgerReportRequest,
    service: ReportService = Depends(get_report_service),
):
    report = await service.generate_ledger(
        payload.account_id,
        payload.from_date,
        payload.to_date,
        payload.save,
    )
    return to_report_response(report)


@router.post("/trial-balance", response_model=FinancialReportResponse)
async def generate_trial_balance(
    payload: TrialBalanceRequest,
    service: ReportService = Depends(get_report_service),
):
    report = await service.generate_trial_balance(payload.as_of_date, payload.save)
    return to_report_response(report)


@router.post("/income-statement", response_model=FinancialReportResponse)
async def generate_income_statement(
    payload: IncomeStatementRequest,
    service: ReportService = Depends(get_report_service),
):
    report = await service.generate_income_statement(
        payload.from_date,
        payload.to_date,
        payload.save,
    )
    return to_report_response(report)


@router.post("/balance-sheet", response_model=FinancialReportResponse)
async def generate_balance_sheet(
    payload: BalanceSheetRequest,
    service: ReportService = Depends(get_report_service),
):
    report = await service.generate_balance_sheet(payload.as_of_date, payload.save)
    return to_report_response(report)


@router.get("/{report_id}", response_model=FinancialReportResponse)
async def get_report(
    report_id: str,
    service: ReportService = Depends(get_report_service),
):
    report = await service.get_report(report_id)
    return to_report_response(report)


@router.get("", response_model=list[FinancialReportResponse])
async def list_reports(
    report_type: ReportType | None = None,
    from_date: date | None = None,
    to_date: date | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    service: ReportService = Depends(get_report_service),
):
    reports = await service.list_reports(report_type, from_date, to_date, skip, limit)
    return [to_report_response(report) for report in reports]
