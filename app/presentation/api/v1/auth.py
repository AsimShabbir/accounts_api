import math

from fastapi import APIRouter, Depends, Query

from app.application.services.auth_service import AuthService
from app.core.config import settings
from app.domain.entities.user_registration import UserRegistration
from app.presentation.auth_dependencies import get_current_user
from app.presentation.dependencies import get_auth_service
from app.presentation.schemas.common import DataTableResponse
from app.presentation.schemas.user_registration import (
    RefreshTokenRequest,
    TokenResponse,
    UserLoginRequest,
    UserRegistrationCreate,
    UserRegistrationResponse,
)

router = APIRouter(tags=["Authentication"])


def _build_datatable(data: list, total: int, page: int, page_size: int) -> DataTableResponse:
    return DataTableResponse(
        data=data,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=max(1, math.ceil(total / page_size)) if page_size else 1,
    )


def _to_user_response(user: UserRegistration) -> UserRegistrationResponse:
    return UserRegistrationResponse(
        id=user.id or "",
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


def _build_token_response(user: UserRegistration, access_token: str, refresh_token: str) -> TokenResponse:
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        refresh_expires_in_days=settings.REFRESH_TOKEN_EXPIRE_DAYS,
        user=_to_user_response(user),
    )


@router.post("/user-registrations", response_model=UserRegistrationResponse, status_code=201)
async def register_user(
    payload: UserRegistrationCreate,
    service: AuthService = Depends(get_auth_service),
):
    user = await service.register_user(payload.model_dump())
    return _to_user_response(user)


@router.get("/user-registrations", response_model=DataTableResponse[UserRegistrationResponse])
async def list_user_registrations(
    is_active: bool | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=500),
    service: AuthService = Depends(get_auth_service),
    _: UserRegistration = Depends(get_current_user),
):
    skip = (page - 1) * page_size
    users, total = await service.list_users(is_active, skip, page_size)
    return _build_datatable(
        [_to_user_response(user) for user in users],
        total,
        page,
        page_size,
    )


@router.post("/auth/login", response_model=TokenResponse)
async def login(
    payload: UserLoginRequest,
    service: AuthService = Depends(get_auth_service),
):
    user, access_token, refresh_token = await service.login(
        payload.username_or_email,
        payload.password,
    )
    return _build_token_response(user, access_token, refresh_token)


@router.post("/auth/refresh", response_model=TokenResponse)
async def refresh_token(
    payload: RefreshTokenRequest,
    service: AuthService = Depends(get_auth_service),
):
    user, access_token, refresh_token = await service.refresh_tokens(payload.refresh_token)
    return _build_token_response(user, access_token, refresh_token)


@router.get("/auth/me", response_model=UserRegistrationResponse)
async def get_me(current_user: UserRegistration = Depends(get_current_user)):
    return _to_user_response(current_user)
