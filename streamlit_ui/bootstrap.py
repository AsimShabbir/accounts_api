import asyncio
import os
from collections.abc import Coroutine
from typing import Any, TypeVar

T = TypeVar("T")

_env_initialized = False
_db_initialized = False


def init_environment() -> None:
    global _env_initialized
    if _env_initialized:
        return

    try:
        import streamlit as st

        secret_keys = [
            "MONGODB_URI",
            "MONGODB_DATABASE",
            "MONGODB_USERNAME",
            "MONGODB_PASSWORD",
            "JWT_SECRET_KEY",
            "JWT_ALGORITHM",
            "ACCESS_TOKEN_EXPIRE_MINUTES",
            "REFRESH_TOKEN_EXPIRE_DAYS",
        ]
        for key in secret_keys:
            if key in st.secrets:
                os.environ.setdefault(key, str(st.secrets[key]))
    except Exception:
        pass

    _env_initialized = True


def run_async(coro: Coroutine[Any, Any, T]) -> T:
    return asyncio.run(coro)


async def ensure_database() -> None:
    global _db_initialized
    if _db_initialized:
        return

    from app.core.database import connect_to_mongodb

    await connect_to_mongodb()
    _db_initialized = True


def bootstrap() -> None:
    init_environment()
    run_async(ensure_database())


def get_auth_service():
    from app.application.services.auth_service import AuthService
    from app.core.database import get_database
    from app.infrastructure.repositories.refresh_token_mongo_repository import MongoRefreshTokenRepository
    from app.infrastructure.repositories.user_registration_mongo_repository import MongoUserRegistrationRepository

    db = get_database()
    return AuthService(MongoUserRegistrationRepository(db), MongoRefreshTokenRepository(db))


def get_chart_of_account_service():
    from app.application.services.chart_of_account_service import ChartOfAccountService
    from app.core.database import get_database
    from app.infrastructure.repositories.chart_of_account_mongo_repository import MongoChartOfAccountRepository

    return ChartOfAccountService(MongoChartOfAccountRepository(get_database()))


def get_voucher_service():
    from app.application.services.voucher_service import VoucherService
    from app.core.database import get_database
    from app.infrastructure.repositories.chart_of_account_mongo_repository import MongoChartOfAccountRepository
    from app.infrastructure.repositories.voucher_mongo_repository import MongoVoucherRepository

    db = get_database()
    return VoucherService(MongoVoucherRepository(db), MongoChartOfAccountRepository(db))


def get_report_service():
    from app.application.services.report_service import ReportService
    from app.core.database import get_database
    from app.infrastructure.repositories.chart_of_account_mongo_repository import MongoChartOfAccountRepository
    from app.infrastructure.repositories.report_mongo_repository import MongoReportRepository
    from app.infrastructure.repositories.voucher_mongo_repository import MongoVoucherRepository

    db = get_database()
    return ReportService(
        MongoChartOfAccountRepository(db),
        MongoVoucherRepository(db),
        MongoReportRepository(db),
    )
