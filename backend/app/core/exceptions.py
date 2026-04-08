from typing import Any


class AppException(Exception):
    def __init__(
        self,
        status_code: int,
        message: str,
        error_code: str = "app_error",
        details: Any | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.message = message
        self.error_code = error_code
        self.details = details


class AuthenticationException(AppException):
    def __init__(self, message: str = "Authentication required", details: Any | None = None) -> None:
        super().__init__(status_code=401, message=message, error_code="authentication_error", details=details)


class AuthorizationException(AppException):
    def __init__(self, message: str = "Insufficient permissions", details: Any | None = None) -> None:
        super().__init__(status_code=403, message=message, error_code="authorization_error", details=details)
