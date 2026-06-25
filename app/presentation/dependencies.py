from fastapi import Depends

from app.application.services.auth_service import AuthService
from app.application.services.chart_of_account_service import ChartOfAccountService
from app.application.services.report_service import ReportService
from app.application.services.voucher_service import VoucherService
from app.core.database import get_database
from app.infrastructure.repositories.chart_of_account_mongo_repository import MongoChartOfAccountRepository
from app.infrastructure.repositories.refresh_token_mongo_repository import MongoRefreshTokenRepository
from app.infrastructure.repositories.user_registration_mongo_repository import MongoUserRegistrationRepository
from app.infrastructure.repositories.report_mongo_repository import MongoReportRepository
from app.infrastructure.repositories.voucher_mongo_repository import MongoVoucherRepository


def get_auth_service() -> AuthService:
    db = get_database()
    repository = MongoUserRegistrationRepository(db)
    refresh_repository = MongoRefreshTokenRepository(db)
    return AuthService(repository, refresh_repository)


def get_chart_of_account_service() -> ChartOfAccountService:
    db = get_database()
    repository = MongoChartOfAccountRepository(db)
    return ChartOfAccountService(repository)


def get_voucher_service() -> VoucherService:
    db = get_database()
    account_repo = MongoChartOfAccountRepository(db)
    voucher_repo = MongoVoucherRepository(db)
    return VoucherService(voucher_repo, account_repo)


def get_report_service() -> ReportService:
    db = get_database()
    account_repo = MongoChartOfAccountRepository(db)
    voucher_repo = MongoVoucherRepository(db)
    report_repo = MongoReportRepository(db)
    return ReportService(account_repo, voucher_repo, report_repo)
