import math
from datetime import date

from fastapi import APIRouter, Depends, Query

from app.application.services.voucher_service import VoucherService
from app.domain.enums import VoucherStatus, VoucherType
from app.presentation.dependencies import get_voucher_service
from app.presentation.schemas.common import DataTableResponse, MessageResponse
from app.presentation.mappers import to_voucher_response
from app.presentation.schemas.voucher import VoucherCreate, VoucherResponse, VoucherUpdate

router = APIRouter(prefix="/vouchers", tags=["Vouchers"])


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
    payload: VoucherCreate,
    service: VoucherService = Depends(get_voucher_service),
):
    voucher = await service.create_voucher(payload.model_dump())
    return to_voucher_response(voucher)


@router.get("", response_model=DataTableResponse[VoucherResponse])
async def list_vouchers(
    status: VoucherStatus | None = None,
    voucher_type: VoucherType | None = None,
    from_date: date | None = None,
    to_date: date | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=500),
    service: VoucherService = Depends(get_voucher_service),
):
    skip = (page - 1) * page_size
    vouchers, total = await service.list_vouchers(
        status, voucher_type, from_date, to_date, skip, page_size
    )
    return _build_datatable(
        [to_voucher_response(voucher) for voucher in vouchers],
        total,
        page,
        page_size,
    )


@router.get("/{voucher_id}", response_model=VoucherResponse)
async def get_voucher(
    voucher_id: str,
    service: VoucherService = Depends(get_voucher_service),
):
    voucher = await service.get_voucher(voucher_id)
    return to_voucher_response(voucher)


@router.put("/{voucher_id}", response_model=VoucherResponse)
async def update_voucher(
    voucher_id: str,
    payload: VoucherUpdate,
    service: VoucherService = Depends(get_voucher_service),
):
    voucher = await service.update_voucher(
        voucher_id,
        payload.model_dump(exclude_unset=True),
    )
    return to_voucher_response(voucher)


@router.post("/{voucher_id}/cancel", response_model=VoucherResponse)
async def cancel_voucher(
    voucher_id: str,
    service: VoucherService = Depends(get_voucher_service),
):
    voucher = await service.cancel_voucher(voucher_id)
    return to_voucher_response(voucher)


@router.post("/{voucher_id}/post", response_model=VoucherResponse)
async def post_voucher(
    voucher_id: str,
    service: VoucherService = Depends(get_voucher_service),
):
    voucher = await service.post_voucher(voucher_id)
    return to_voucher_response(voucher)
