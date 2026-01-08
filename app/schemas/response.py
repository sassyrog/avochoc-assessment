from typing import Any, Generic, Optional, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")


class SuccessResponse(BaseModel, Generic[T]):
    """Standard success response"""

    message: str
    code: int = 200
    data: T


class ErrorResponse(BaseModel):
    """Standard error response"""

    reason: str
    code: int
    data: Optional[Any] = None


class PaginationMeta(BaseModel):
    """Pagination metadata"""

    page: int = Field(..., ge=1)
    page_size: int = Field(..., ge=1)
    total: int = Field(..., ge=0)
    total_pages: int = Field(..., ge=0)


class PaginatedResponse(BaseModel, Generic[T]):
    """Success response with pagination"""

    message: str
    code: int = 200
    page: int = Field(..., ge=1)
    page_size: int = Field(..., ge=1)
    total: int = Field(..., ge=0)
    total_pages: int = Field(..., ge=0)
    data: list[T]
