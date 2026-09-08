"""
Application Custom Exceptions and Global Error Handlers.
"""

from typing import Any, Dict, Optional
from fastapi import Request, status
from fastapi.responses import JSONResponse


class AppException(Exception):
    """Base exception for application errors."""

    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details or {}


class ServiceNotImplementedException(AppException):
    """Raised when an AI service interface is called before algorithm implementation."""

    def __init__(
        self,
        service_name: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        message = f"Service '{service_name}' interface is registered but algorithm is not implemented yet in this phase."
        super().__init__(
            message=message,
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            details=details or {"service": service_name, "phase": "foundation"},
        )


class ValidationException(AppException):
    """Raised when validation fails for business rules or profiles."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details,
        )


class ProviderConfigurationException(AppException):
    """Raised when an externally configured provider cannot be used safely."""

    def __init__(self, provider_name: str):
        super().__init__(
            message=f"{provider_name} is not configured.",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            details={"provider": provider_name},
        )


class ProviderResponseException(AppException):
    """Raised when a provider response is malformed or unavailable."""

    def __init__(self, provider_name: str):
        super().__init__(
            message=f"{provider_name} returned an unusable response.",
            status_code=status.HTTP_502_BAD_GATEWAY,
            details={"provider": provider_name},
        )


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """Global handler for AppException subclasses."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "message": exc.message,
                "status_code": exc.status_code,
                "details": exc.details,
            },
        },
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Fallback handler for unhandled exceptions."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": {
                "message": "An unexpected server error occurred.",
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "details": {"error_type": type(exc).__name__},
            },
        },
    )
