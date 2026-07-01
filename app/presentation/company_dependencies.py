from bson import ObjectId
from bson.errors import InvalidId
from fastapi import Depends, Query

from app.application.exceptions import ValidationError
from app.application.services.company_service import CompanyService
from app.domain.entities.user_registration import UserRegistration
from app.presentation.auth_dependencies import get_current_user
from app.presentation.dependencies import get_company_service


def is_mongo_object_id(value: str) -> bool:
    try:
        ObjectId(value)
        return len(value) == 24
    except (InvalidId, TypeError):
        return False


async def _resolve_company_document_id(
    company_id: str,
    current_user: UserRegistration,
    service: CompanyService,
) -> str:
    if not is_mongo_object_id(company_id):
        raise ValidationError(
            "Invalid company_id. Use the company `id` from GET /api/v1/companies "
            f"(24-character document id), not the slug '{company_id}'."
        )
    await service.get_company(current_user, company_id)
    return company_id


async def get_validated_company_id_query(
    company_id: str = Query(..., description="Company document id from GET /companies"),
    current_user: UserRegistration = Depends(get_current_user),
    service: CompanyService = Depends(get_company_service),
) -> str:
    return await _resolve_company_document_id(company_id, current_user, service)


async def get_validated_company_id_path(
    company_id: str,
    current_user: UserRegistration = Depends(get_current_user),
    service: CompanyService = Depends(get_company_service),
) -> str:
    return await _resolve_company_document_id(company_id, current_user, service)
