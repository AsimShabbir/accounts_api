import math

from fastapi import APIRouter, Depends, Query

from app.application.services.chart_of_account_service import ChartOfAccountService
from app.domain.enums import AccountType
from app.presentation.dependencies import get_chart_of_account_service
from app.presentation.schemas.chart_of_account import (
    ChartOfAccountCreate,
    ChartOfAccountResponse,
    ChartOfAccountUpdate,
)
from app.presentation.schemas.common import DataTableResponse, MessageResponse

router = APIRouter(prefix="/chart-of-accounts", tags=["Chart of Accounts"])


def _build_datatable(data: list, total: int, page: int, page_size: int) -> DataTableResponse:
    return DataTableResponse(
        data=data,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=max(1, math.ceil(total / page_size)) if page_size else 1,
    )


@router.post("", response_model=ChartOfAccountResponse, status_code=201)
async def create_account(
    payload: ChartOfAccountCreate,
    service: ChartOfAccountService = Depends(get_chart_of_account_service),
):
    account = await service.create_account(payload.model_dump())
    return ChartOfAccountResponse.model_validate(account)


@router.get("", response_model=DataTableResponse[ChartOfAccountResponse])
async def list_accounts(
    account_type: AccountType | None = None,
    is_active: bool | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=500),
    service: ChartOfAccountService = Depends(get_chart_of_account_service),
):
    skip = (page - 1) * page_size
    accounts, total = await service.list_accounts(account_type, is_active, skip, page_size)
    return _build_datatable(
        [ChartOfAccountResponse.model_validate(account) for account in accounts],
        total,
        page,
        page_size,
    )


@router.get("/{account_id}", response_model=ChartOfAccountResponse)
async def get_account(
    account_id: str,
    service: ChartOfAccountService = Depends(get_chart_of_account_service),
):
    account = await service.get_account(account_id)
    return ChartOfAccountResponse.model_validate(account)


@router.put("/{account_id}", response_model=ChartOfAccountResponse)
async def update_account(
    account_id: str,
    payload: ChartOfAccountUpdate,
    service: ChartOfAccountService = Depends(get_chart_of_account_service),
):
    account = await service.update_account(
        account_id,
        payload.model_dump(exclude_unset=True),
    )
    return ChartOfAccountResponse.model_validate(account)


@router.delete("/{account_id}", response_model=MessageResponse)
async def delete_account(
    account_id: str,
    service: ChartOfAccountService = Depends(get_chart_of_account_service),
):
    await service.delete_account(account_id)
    return MessageResponse(message="Account deleted successfully")
