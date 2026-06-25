from datetime import datetime
from decimal import Decimal
from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class DataTableResponse(BaseModel, Generic[T]):
    data: list[T]
    total: int
    page: int
    page_size: int
    total_pages: int


class MessageResponse(BaseModel):
    message: str
    success: bool = True


class DecimalSerializerMixin(BaseModel):
    @classmethod
    def serialize_decimal(cls, value: Decimal) -> str:
        return f"{value:.2f}"
