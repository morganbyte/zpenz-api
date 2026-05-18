from fastapi import status


class AppException(Exception):
    """Base exception for application errors."""

    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    detail = "Internal server error"

    def __init__(self, detail=None):
        if detail:
            self.detail = detail
        super().__init__(self.detail)


class ValidationError(AppException):
    """Raised when request data validation fails."""

    status_code = status.HTTP_400_BAD_REQUEST
    detail = "Validation error"


class AuthenticationError(AppException):
    """Raised when authentication fails."""

    status_code = status.HTTP_401_UNAUTHORIZED
    detail = "Authentication failed"


class NotFoundError(AppException):
    """Raised when a resource is not found."""

    status_code = status.HTTP_404_NOT_FOUND
    detail = "Resource not found"


class ConflictError(AppException):
    """Raised when there's a conflict (e.g., duplicate resource)."""

    status_code = status.HTTP_409_CONFLICT
    detail = "Resource conflict"
