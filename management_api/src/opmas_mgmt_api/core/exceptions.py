from typing import Any, Dict, Optional

from fastapi import HTTPException, status


class OPMASException(HTTPException):
    """Base exception for OPMAS Management API"""

    def __init__(
        self,
        detail: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        headers: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(status_code=status_code, detail=detail, headers=headers)


class ValidationError(OPMASException):
    """Raised when input validation fails"""

    def __init__(self, detail: str):
        super().__init__(detail=detail, status_code=status.HTTP_400_BAD_REQUEST)


class AuthenticationError(OPMASException):
    """Raised when authentication fails"""

    def __init__(self, detail: str):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_401_UNAUTHORIZED,
            headers={"WWW-Authenticate": "Bearer"},
        )


class AuthorizationError(OPMASException):
    """Raised when user lacks required permissions"""

    def __init__(self, detail: str):
        super().__init__(detail=detail, status_code=status.HTTP_403_FORBIDDEN)


class ResourceNotFoundError(OPMASException):
    """Raised when a requested resource is not found"""

    def __init__(self, detail: str):
        super().__init__(detail=detail, status_code=status.HTTP_404_NOT_FOUND)


class ConflictError(OPMASException):
    """Raised when there's a conflict with existing resources"""

    def __init__(self, detail: str):
        super().__init__(detail=detail, status_code=status.HTTP_409_CONFLICT)


class DatabaseError(OPMASException):
    """Raised when database operations fail"""

    def __init__(self, detail: str):
        super().__init__(detail=detail, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PlaybookExecutionError(OPMASException):
    """Raised when playbook execution fails"""

    def __init__(self, detail: str):
        super().__init__(detail=detail, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AgentCommunicationError(OPMASException):
    """Raised when communication with agents fails"""

    def __init__(self, detail: str):
        super().__init__(detail=detail, status_code=status.HTTP_503_SERVICE_UNAVAILABLE)


class ConfigurationError(OPMASException):
    """Raised when configuration is invalid or missing"""

    def __init__(self, detail: str):
        super().__init__(detail=detail, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
