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
