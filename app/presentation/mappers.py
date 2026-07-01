from app.domain.entities.report import FinancialReport
from app.domain.entities.voucher import Voucher
from app.presentation.schemas.report import FinancialReportResponse, ReportLineItemResponse
from app.presentation.schemas.voucher import VoucherEntryResponse, VoucherResponse


def to_voucher_response(voucher: Voucher) -> VoucherResponse:
    return VoucherResponse(
        id=voucher.id or "",
        company_id=voucher.company_id,
        voucher_number=voucher.voucher_number,
        voucher_type=voucher.voucher_type,
        voucher_date=voucher.voucher_date,
        reference=voucher.reference,
        narration=voucher.narration,
        status=voucher.status,
        entries=[VoucherEntryResponse.model_validate(entry.model_dump()) for entry in voucher.entries],
        total_debit=voucher.total_debit,
        total_credit=voucher.total_credit,
        posted_at=voucher.posted_at,
        cancelled_at=voucher.cancelled_at,
        created_at=voucher.created_at,
        updated_at=voucher.updated_at,
    )


def to_report_response(report: FinancialReport) -> FinancialReportResponse:
    return FinancialReportResponse(
        id=report.id or "",
        company_id=report.company_id,
        report_type=report.report_type,
        report_title=report.report_title,
        from_date=report.from_date,
        to_date=report.to_date,
        report_date=report.report_date,
        account_id=report.account_id,
        account_code=report.account_code,
        line_items=[ReportLineItemResponse.model_validate(item.model_dump()) for item in report.line_items],
        totals=report.totals,
        generated_at=report.generated_at,
        parameters=report.parameters,
    )
