from abc import ABC, abstractmethod

from app.domain.entities.company import Company


class CompanyRepository(ABC):
    @abstractmethod
    async def create(self, company: Company) -> Company:
        pass

    @abstractmethod
    async def get_by_id(self, company_id: str) -> Company | None:
        pass

    @abstractmethod
    async def get_by_company_id(self, company_id: str, user_id: str) -> Company | None:
        pass

    @abstractmethod
    async def get_for_user(self, company_key: str, user_id: str) -> Company | None:
        """Resolve a company by business slug (company_id) or MongoDB document id."""
        pass

    @abstractmethod
    async def list_by_user(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Company]:
        pass

    @abstractmethod
    async def count_by_user(self, user_id: str) -> int:
        pass

    @abstractmethod
    async def update(self, company_id: str, company: Company) -> Company | None:
        pass

    @abstractmethod
    async def delete(self, company_id: str) -> bool:
        pass
