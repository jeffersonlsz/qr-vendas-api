"""
Custom exceptions for the application.
Provides consistent error handling across the API.
"""

from typing import Any, Optional


class AppException(Exception):
    """Base exception for all application exceptions."""

    def __init__(
        self,
        message: str = "An error occurred",
        status_code: int = 500,
        detail: Optional[Any] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.detail = detail
        super().__init__(self.message)


class NotFoundException(AppException):
    """Resource not found exception."""

    def __init__(self, resource: str, identifier: Optional[str] = None):
        message = f"{resource} not found"
        detail = f"{resource} with ID {identifier} not found" if identifier else message
        super().__init__(message=message, status_code=404, detail=detail)


class ConflictException(AppException):
    """Resource conflict exception (e.g., duplicate)."""

    def __init__(self, message: str = "Resource conflict"):
        super().__init__(message=message, status_code=409)


class ValidationException(AppException):
    """Business validation exception."""

    def __init__(self, message: str = "Validation failed"):
        super().__init__(message=message, status_code=422)


class UnauthorizedException(AppException):
    """Authentication/authorization exception."""

    def __init__(self, message: str = "Unauthorized"):
        super().__init__(message=message, status_code=401)


class ForbiddenException(AppException):
    """Access forbidden exception."""

    def __init__(self, message: str = "Access forbidden"):
        super().__init__(message=message, status_code=403)


class DatabaseException(AppException):
    """Database operation exception."""

    def __init__(self, message: str = "Database error"):
        super().__init__(message=message, status_code=500)
