from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.application.exceptions import UnauthorizedError
from app.application.services.auth_service import AuthService
from app.core.security import decode_access_token
from app.domain.entities.user_registration import UserRegistration
from app.presentation.dependencies import get_auth_service

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    service: AuthService = Depends(get_auth_service),
) -> UserRegistration:
    if not credentials:
        raise UnauthorizedError("Not authenticated. Provide a valid Bearer token.")

    try:
        payload = decode_access_token(credentials.credentials)
        user_id = payload.get("sub")
        if not user_id:
            raise UnauthorizedError("Invalid token")
        user = await service.get_user(user_id)
        if not user.is_active:
            raise UnauthorizedError("User account is inactive")
        return user
    except ValueError as exc:
        raise UnauthorizedError(str(exc)) from exc
