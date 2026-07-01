from datetime import datetime

from app.application.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.domain.entities.company import Company
from app.domain.entities.user_registration import UserRegistration
from app.domain.repositories.company_repository import CompanyRepository


class CompanyService:
    def __init__(self, repository: CompanyRepository) -> None:
        self._repository = repository

    async def create_company(self, user: UserRegistration, data: dict) -> Company:
        slug = (data.get("slug") or data.get("company_id", "")).strip().lower()
        existing = await self._repository.get_by_company_id(slug, user.id or "")
        if existing:
            raise ConflictError(f"Company slug '{slug}' already exists for this user")

        company = Company(
            company_id=slug,
            name=data["name"],
            address=data["address"],
            logo=data["logo"],
            favicon=data["favicon"],
            user_id=user.id or "",
        )
        return await self._repository.create(company)

    async def get_company(self, user: UserRegistration, company_id: str) -> Company:
        company = await self._repository.get_for_user(company_id, user.id or "")
        if not company:
            raise NotFoundError("Company not found")
        return company

    async def list_companies(
        self,
        user: UserRegistration,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[Company], int]:
        companies = await self._repository.list_by_user(user.id or "", skip, limit)
        total = await self._repository.count_by_user(user.id or "")
        return companies, total

    async def update_company(
        self,
        user: UserRegistration,
        company_id: str,
        data: dict,
    ) -> Company:
        company = await self.get_company(user, company_id)

        if "slug" in data or "company_id" in data:
            new_slug = (data.get("slug") or data.get("company_id", "")).strip().lower()
            if new_slug != company.company_id:
                existing = await self._repository.get_by_company_id(new_slug, user.id or "")
                if existing and existing.id != company.id:
                    raise ConflictError(f"Company slug '{new_slug}' already exists for this user")
                company.company_id = new_slug

        if "name" in data:
            company.name = data["name"]
        if "address" in data:
            company.address = data["address"]
        if "logo" in data:
            company.logo = data["logo"]
        if "favicon" in data:
            company.favicon = data["favicon"]

        company.updated_at = datetime.utcnow()
        updated = await self._repository.update(company.id or "", company)
        if not updated:
            raise NotFoundError("Company not found")
        return updated

    async def delete_company(self, user: UserRegistration, company_id: str) -> None:
        company = await self.get_company(user, company_id)
        deleted = await self._repository.delete(company.id or "")
        if not deleted:
            raise NotFoundError("Company not found")

    def _ensure_owner(self, user: UserRegistration, company: Company) -> None:
        if company.user_id != (user.id or ""):
            raise ForbiddenError("You do not have access to this company")
