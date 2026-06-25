import re
from datetime import datetime, timezone

from app.application.exceptions import ConflictError, UnauthorizedError, ValidationError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    hash_password,
    verify_password,
)
from app.domain.entities.refresh_token import RefreshToken
from app.domain.entities.user_registration import UserRegistration
from app.domain.repositories.refresh_token_repository import RefreshTokenRepository
from app.domain.repositories.user_registration_repository import UserRegistrationRepository

USERNAME_PATTERN = re.compile(r"^[a-zA-Z0-9_]{3,30}$")


class AuthService:
    def __init__(
        self,
        repository: UserRegistrationRepository,
        refresh_token_repository: RefreshTokenRepository,
    ) -> None:
        self._repository = repository
        self._refresh_tokens = refresh_token_repository

    async def register_user(self, data: dict) -> UserRegistration:
        username = data["username"].strip().lower()
        email = data["email"].strip().lower()
        password = data["password"]

        if not USERNAME_PATTERN.match(username):
            raise ValidationError("Username must be 3-30 characters (letters, numbers, underscore only)")

        if len(password) < 6:
            raise ValidationError("Password must be at least 6 characters")

        if await self._repository.get_by_email(email):
            raise ConflictError("Email is already registered")

        if await self._repository.get_by_username(username):
            raise ConflictError("Username is already taken")

        user = UserRegistration(
            username=username,
            email=email,
            full_name=data["full_name"].strip(),
            password_hash=hash_password(password),
        )
        return await self._repository.create(user)

    async def login(self, username_or_email: str, password: str) -> tuple[UserRegistration, str, str]:
        identifier = username_or_email.strip().lower()
        user = await self._repository.get_by_email(identifier)
        if not user:
            user = await self._repository.get_by_username(identifier)

        if not user or not verify_password(password, user.password_hash):
            raise UnauthorizedError("Invalid email/username or password")

        if not user.is_active:
            raise UnauthorizedError("User account is inactive")

        return await self._issue_tokens(user)

    async def refresh_tokens(self, refresh_token: str) -> tuple[UserRegistration, str, str]:
        try:
            payload = decode_refresh_token(refresh_token)
        except ValueError as exc:
            raise UnauthorizedError(str(exc)) from exc

        jti = payload.get("jti")
        user_id = payload.get("sub")
        if not jti or not user_id:
            raise UnauthorizedError("Invalid refresh token")

        stored = await self._refresh_tokens.get_by_jti(jti)
        if not stored:
            raise UnauthorizedError("Refresh token is invalid or has been revoked")

        if stored.expires_at.tzinfo is None:
            expires_at = stored.expires_at.replace(tzinfo=timezone.utc)
        else:
            expires_at = stored.expires_at

        if expires_at < datetime.now(timezone.utc):
            await self._refresh_tokens.revoke(jti)
            raise UnauthorizedError("Refresh token has expired")

        user = await self._repository.get_by_id(user_id)
        if not user or not user.is_active:
            await self._refresh_tokens.revoke(jti)
            raise UnauthorizedError("User account is inactive or not found")

        await self._refresh_tokens.revoke(jti)
        return await self._issue_tokens(user)

    async def get_user(self, user_id: str) -> UserRegistration:
        user = await self._repository.get_by_id(user_id)
        if not user:
            raise UnauthorizedError("User not found")
        return user

    async def list_users(
        self,
        is_active: bool | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[UserRegistration], int]:
        users = await self._repository.list_all(is_active, skip, limit)
        total = await self._repository.count(is_active)
        return users, total

    async def _issue_tokens(self, user: UserRegistration) -> tuple[UserRegistration, str, str]:
        user_id = user.id or ""
        access_token = create_access_token(
            subject=user_id,
            extra_claims={"username": user.username, "email": user.email},
        )
        refresh_token, jti, expires_at = create_refresh_token(user_id)
        await self._refresh_tokens.create(
            RefreshToken(user_id=user_id, jti=jti, expires_at=expires_at),
        )
        return user, access_token, refresh_token
