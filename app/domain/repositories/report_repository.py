from abc import ABC, abstractmethod
from datetime import date

from app.domain.entities.report import FinancialReport
from app.domain.enums import ReportType


class ReportRepository(ABC):
    @abstractmethod
    async def save(self, report: FinancialReport) -> FinancialReport:
        pass

    @abstractmethod
    async def get_by_id(self, report_id: str) -> FinancialReport | None:
        pass

    @abstractmethod
    async def list_reports(
        self,
        report_type: ReportType | None = None,
        from_date: date | None = None,
        to_date: date | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[FinancialReport]:
        pass
