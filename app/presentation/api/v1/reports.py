from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.application.services.report_service import ReportService
from app.domain.entities.user_registration import UserRegistration
from app.domain.enums import ReportType
from app.presentation.auth_dependencies import get_current_user
from app.presentation.company_dependencies import get_validated_company_id_query
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

CompanyId = Annotated[str, Depends(get_validated_company_id_query)]


@router.post("/ledger", response_model=FinancialReportResponse)
async def generate_ledger(
    company_id: CompanyId,
    payload: LedgerReportRequest,
    current_user: UserRegistration = Depends(get_current_user),
    service: ReportService = Depends(get_report_service),
):
    report = await service.generate_ledger(
        current_user,
        company_id,
        payload.account_id,
        payload.from_date,
        payload.to_date,
        payload.save,
    )
    return to_report_response(report)


@router.post("/trial-balance", response_model=FinancialReportResponse)
async def generate_trial_balance(
    company_id: CompanyId,
    payload: TrialBalanceRequest,
    current_user: UserRegistration = Depends(get_current_user),
    service: ReportService = Depends(get_report_service),
):
    report = await service.generate_trial_balance(
        current_user,
        company_id,
        payload.as_of_date,
        payload.save,
    )
    return to_report_response(report)


@router.post("/income-statement", response_model=FinancialReportResponse)
async def generate_income_statement(
    company_id: CompanyId,
    payload: IncomeStatementRequest,
    current_user: UserRegistration = Depends(get_current_user),
    service: ReportService = Depends(get_report_service),
):
    report = await service.generate_income_statement(
        current_user,
        company_id,
        payload.from_date,
        payload.to_date,
        payload.save,
    )
    return to_report_response(report)


@router.post("/balance-sheet", response_model=FinancialReportResponse)
async def generate_balance_sheet(
    company_id: CompanyId,
    payload: BalanceSheetRequest,
    current_user: UserRegistration = Depends(get_current_user),
    service: ReportService = Depends(get_report_service),
):
    report = await service.generate_balance_sheet(
        current_user,
        company_id,
        payload.as_of_date,
        payload.save,
    )
    return to_report_response(report)


@router.get("", response_model=list[FinancialReportResponse])
async def list_reports(
    company_id: CompanyId,
    report_type: ReportType | None = None,
    from_date: date | None = None,
    to_date: date | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: UserRegistration = Depends(get_current_user),
    service: ReportService = Depends(get_report_service),
):
    reports = await service.list_reports(
        current_user,
        company_id,
        report_type,
        from_date,
        to_date,
        skip,
        limit,
    )
    return [to_report_response(report) for report in reports]


@router.get("/{report_id}", response_model=FinancialReportResponse)
async def get_report(
    company_id: CompanyId,
    report_id: str,
    current_user: UserRegistration = Depends(get_current_user),
    service: ReportService = Depends(get_report_service),
):
    report = await service.get_report(current_user, company_id, report_id)
    return to_report_response(report)

