from abc import ABC, abstractmethod

from app.domain.entities.refresh_token import RefreshToken


class RefreshTokenRepository(ABC):
    @abstractmethod
    async def create(self, token: RefreshToken) -> RefreshToken:
        pass

    @abstractmethod
    async def get_by_jti(self, jti: str) -> RefreshToken | None:
        pass

    @abstractmethod
    async def revoke(self, jti: str) -> None:
        pass
