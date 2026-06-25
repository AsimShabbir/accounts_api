from abc import ABC, abstractmethod

from app.domain.entities.user_registration import UserRegistration


class UserRegistrationRepository(ABC):
    @abstractmethod
    async def create(self, user: UserRegistration) -> UserRegistration:
        pass

    @abstractmethod
    async def get_by_id(self, user_id: str) -> UserRegistration | None:
        pass

    @abstractmethod
    async def get_by_email(self, email: str) -> UserRegistration | None:
        pass

    @abstractmethod
    async def get_by_username(self, username: str) -> UserRegistration | None:
        pass

    @abstractmethod
    async def list_all(
        self,
        is_active: bool | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[UserRegistration]:
        pass

    @abstractmethod
    async def count(self, is_active: bool | None = None) -> int:
        pass
