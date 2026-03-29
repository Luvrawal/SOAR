from typing import Any

from pydantic import BaseModel, Field


class ApiResponse(BaseModel):
    success: bool = True
    message: str = "Request completed successfully"
    data: dict[str, Any] | None = None


class ApiErrorResponse(BaseModel):
    success: bool = False
    message: str = "Request failed"
    error_code: str = Field(default="internal_error")
    details: Any | None = None
