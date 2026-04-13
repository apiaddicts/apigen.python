from pydantic import BaseModel, Field
from typing import Generic, TypeVar, List

T = TypeVar('T')


class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T] = Field(serialization_alias="results")
    total: int = Field(serialization_alias="total")
    page: int = Field(serialization_alias="currentCount")
    per_page: int = Field(serialization_alias="pageSize")
    total_pages: int = Field(serialization_alias="pageCount")