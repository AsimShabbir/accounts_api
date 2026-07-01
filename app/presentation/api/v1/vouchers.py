import math
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.application.services.voucher_service import VoucherService
from app.domain.entities.user_registration import UserRegistration
from app.domain.enums import VoucherStatus, VoucherType
from app.presentation.auth_dependencies import get_current_user
from app.presentation.company_dependencies import get_validated_company_id_query
from app.presentation.dependencies import get_voucher_service
from app.presentation.schemas.common import DataTableResponse
from app.presentation.mappers import to_voucher_response
from app.presentation.schemas.voucher import VoucherCreate, VoucherResponse, VoucherUpdate

router = APIRouter(prefix="/vouchers", tags=["Vouchers"])

CompanyId = Annotated[str, Depends(get_validated_company_id_query)]


def _build_datatable(data: list, total: int, page: int, page_size: int) -> DataTableResponse:
    return DataTableResponse(
        data=data,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=max(1, math.ceil(total / page_size)) if page_size else 1,
    )


@router.post("", response_model=VoucherResponse, status_code=201)
async def create_voucher(
    company_id: CompanyId,
    payload: VoucherCreate,
    current_user: UserRegistration = Depends(get_current_user),
    service: VoucherService = Depends(get_voucher_service),
):
    voucher = await service.create_voucher(current_user, company_id, payload.model_dump())
    return to_voucher_response(voucher)


@router.get("", response_model=DataTableResponse[VoucherResponse])
async def list_vouchers(
    company_id: CompanyId,
    status: VoucherStatus | None = None,
    voucher_type: VoucherType | None = None,
    from_date: date | None = None,
    to_date: date | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=500),
    current_user: UserRegistration = Depends(get_current_user),
    service: VoucherService = Depends(get_voucher_service),
):
    skip = (page - 1) * page_size
    vouchers, total = await service.list_vouchers(
        current_user,
        company_id,
        status,
        voucher_type,
        from_date,
        to_date,
        skip,
        page_size,
    )
    return _build_datatable(
        [to_voucher_response(voucher) for voucher in vouchers],
        total,
        page,
        page_size,
    )


@router.get("/{voucher_id}", response_model=VoucherResponse)
async def get_voucher(
    company_id: CompanyId,
    voucher_id: str,
    current_user: UserRegistration = Depends(get_current_user),
    service: VoucherService = Depends(get_voucher_service),
):
    voucher = await service.get_voucher(current_user, company_id, voucher_id)
    return to_voucher_response(voucher)


@router.put("/{voucher_id}", response_model=VoucherResponse)
async def update_voucher(
    company_id: CompanyId,
    voucher_id: str,
    payload: VoucherUpdate,
    current_user: UserRegistration = Depends(get_current_user),
    service: VoucherService = Depends(get_voucher_service),
):
    voucher = await service.update_voucher(
        current_user,
        company_id,
        voucher_id,
        payload.model_dump(exclude_unset=True),
    )
    return to_voucher_response(voucher)


@router.post("/{voucher_id}/cancel", response_model=VoucherResponse)
async def cancel_voucher(
    company_id: CompanyId,
    voucher_id: str,
    current_user: UserRegistration = Depends(get_current_user),
    service: VoucherService = Depends(get_voucher_service),
):
    voucher = await service.cancel_voucher(current_user, company_id, voucher_id)
    return to_voucher_response(voucher)


@router.post("/{voucher_id}/post", response_model=VoucherResponse)
async def post_voucher(
    company_id: CompanyId,
    voucher_id: str,
    current_user: UserRegistration = Depends(get_current_user),
    service: VoucherService = Depends(get_voucher_service),
):
    voucher = await service.post_voucher(current_user, company_id, voucher_id)
    return to_voucher_response(voucher)
