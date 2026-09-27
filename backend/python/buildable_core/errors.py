import logging
from collections.abc import Sequence
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class AppError(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        *,
        status_code: int = 400,
        details: Sequence[dict[str, Any]] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = list(details or [])


def _error_body(request: Request, error: AppError) -> dict[str, Any]:
    return {
        "success": False,
        "error": {
            "code": error.code,
            "message": error.message,
            "details": error.details,
        },
        "meta": {"requestId": getattr(request.state, "request_id", None)},
    }


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def handle_app_error(request: Request, error: AppError) -> JSONResponse:
        return JSONResponse(_error_body(request, error), status_code=error.status_code)

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        request: Request, error: RequestValidationError
    ) -> JSONResponse:
        details = [
            {"path": ".".join(str(part) for part in item["loc"]), "message": item["msg"]}
            for item in error.errors()
        ]
        app_error = AppError(
            "validation_error",
            "The request contains invalid values.",
            status_code=422,
            details=details,
        )
        return JSONResponse(_error_body(request, app_error), status_code=422)

    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, error: Exception) -> JSONResponse:
        logger.exception("unhandled_request_error", extra={"request_id": request.state.request_id})
        app_error = AppError(
            "internal_error", "The server could not complete the request.", status_code=500
        )
        return JSONResponse(_error_body(request, app_error), status_code=500)
