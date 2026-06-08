"""
Common response schemas used across the API.
"""

from typing import Any, Generic, Optional, TypeVar, List

from pydantic import BaseModel, Field

T = TypeVar("T")


class ResponseBase(BaseModel):
    """Base response schema."""

    success: bool = True
    message: Optional[str] = None


class DataResponse(ResponseBase, Generic[T]):
    """Response with data payload."""

    data: Optional[T] = None


class PaginatedResponse(DataResponse[T], Generic[T]):
    """Paginated response."""

    data: List[T]  # ✅ sobrescreve o Optional[T]

    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    total: int = 0
    has_more: bool = False


class ErrorResponse(ResponseBase):
    """Error response schema."""

    success: bool = False
    error_code: Optional[str] = None
    detail: Optional[Any] = None


class HealthCheckResponse(BaseModel):
    """Health check response."""

    status: str = "healthy"
    version: str
    environment: str
    database: str = "connected"
