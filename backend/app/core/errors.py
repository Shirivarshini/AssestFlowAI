"""
Standard error handling.

SOURCE: 04_API_CONTRACT.md "Standard error" shape:
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Human-readable message",
    "details": {}
  }
}
"""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class AppError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400, details: dict | None = None):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}


class NotFoundError(AppError):
    def __init__(self, message: str, details: dict | None = None):
        super().__init__("NOT_FOUND", message, 404, details)


class ValidationError(AppError):
    def __init__(self, message: str, details: dict | None = None):
        super().__init__("VALIDATION_ERROR", message, 422, details)


class ConflictError(AppError):
    def __init__(self, message: str, details: dict | None = None):
        super().__init__("CONFLICT", message, 409, details)


class InvalidTransitionError(AppError):
    def __init__(self, message: str, details: dict | None = None):
        super().__init__("INVALID_TRANSITION", message, 409, details)


class OverLeverageError(AppError):
    def __init__(self, message: str, details: dict | None = None):
        super().__init__("OVER_LEVERAGE", message, 409, details)


def _error_body(code: str, message: str, details: dict) -> dict:
    return {"error": {"code": code, "message": message, "details": details}}


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError):
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_body(exc.code, exc.message, exc.details),
        )

    @app.exception_handler(Exception)
    async def unhandled_error_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=500,
            content=_error_body("INTERNAL_ERROR", "An unexpected error occurred.", {}),
        )
