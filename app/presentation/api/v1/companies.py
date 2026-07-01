import math
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.application.services.company_service import CompanyService
from app.domain.entities.user_registration import UserRegistration
from app.presentation.auth_dependencies import get_current_user
from app.presentation.company_dependencies import get_validated_company_id_path
from app.presentation.dependencies import get_company_service
from app.presentation.schemas.common import DataTableResponse, MessageResponse
from app.presentation.schemas.company import CompanyCreate, CompanyResponse, CompanyUpdate

router = APIRouter(prefix="/companies", tags=["Companies"])

CompanyDocId = Annotated[str, Depends(get_validated_company_id_path)]


def _build_datatable(data: list, total: int, page: int, page_size: int) -> DataTableResponse:
    return DataTableResponse(
        data=data,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=max(1, math.ceil(total / page_size)) if page_size else 1,
    )


@router.post("", response_model=CompanyResponse, status_code=201)
async def create_company(
    payload: CompanyCreate,
    current_user: UserRegistration = Depends(get_current_user),
    service: CompanyService = Depends(get_company_service),
):
    company = await service.create_company(current_user, payload.model_dump())
    return CompanyResponse.from_company(company)


@router.get("", response_model=DataTableResponse[CompanyResponse])
async def list_companies(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=500),
    current_user: UserRegistration = Depends(get_current_user),
    service: CompanyService = Depends(get_company_service),
):
    skip = (page - 1) * page_size
    companies, total = await service.list_companies(current_user, skip, page_size)
    return _build_datatable(
        [CompanyResponse.from_company(company) for company in companies],
        total,
        page,
        page_size,
    )


@router.get("/{company_id}", response_model=CompanyResponse)
async def get_company(
    company_id: CompanyDocId,
    current_user: UserRegistration = Depends(get_current_user),
    service: CompanyService = Depends(get_company_service),
):
    company = await service.get_company(current_user, company_id)
    return CompanyResponse.from_company(company)


@router.put("/{company_id}", response_model=CompanyResponse)
async def update_company(
    company_id: CompanyDocId,
    payload: CompanyUpdate,
    current_user: UserRegistration = Depends(get_current_user),
    service: CompanyService = Depends(get_company_service),
):
    company = await service.update_company(
        current_user,
        company_id,
        payload.model_dump(exclude_unset=True),
    )
    return CompanyResponse.from_company(company)


@router.delete("/{company_id}", response_model=MessageResponse)
async def delete_company(
    company_id: CompanyDocId,
    current_user: UserRegistration = Depends(get_current_user),
    service: CompanyService = Depends(get_company_service),
):
    await service.delete_company(current_user, company_id)
    return MessageResponse(message="Company deleted successfully")
