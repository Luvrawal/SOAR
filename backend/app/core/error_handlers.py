import logging

from fastapi import FastAPI, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from app.core.exceptions import AppException
from app.schemas.common import ApiErrorResponse

logger = logging.getLogger(__name__)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppException)
    async def app_exception_handler(_, exc: AppException) -> JSONResponse:
        payload = ApiErrorResponse(
            message=exc.message,
            error_code=exc.error_code,
            details=exc.details,
        )
        return JSONResponse(status_code=exc.status_code, content=payload.model_dump())

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(_, exc: RequestValidationError) -> JSONResponse:
        payload = ApiErrorResponse(
            message="Validation error",
            error_code="validation_error",
            details=exc.errors(),
        )
        return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content=payload.model_dump())

    @app.exception_handler(SQLAlchemyError)
    async def sqlalchemy_exception_handler(_, __: SQLAlchemyError) -> JSONResponse:
        logger.exception("Database operation failed")
        payload = ApiErrorResponse(
            message="Database error",
            error_code="database_error",
        )
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=payload.model_dump())

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(_, __: Exception) -> JSONResponse:
        logger.exception("Unhandled server error")
        payload = ApiErrorResponse(
            message="Internal server error",
            error_code="internal_error",
        )
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=payload.model_dump())
