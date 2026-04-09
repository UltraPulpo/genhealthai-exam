"""Custom exception hierarchy and Flask error handlers."""

from __future__ import annotations

import logging

from flask import Flask, jsonify
from werkzeug.exceptions import RequestEntityTooLarge

logger = logging.getLogger(__name__)


class AppError(Exception):
    """Base application error."""

    code: str = "APP_ERROR"
    status_code: int = 500

    def __init__(self, message: str, *, details: list[dict] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details: list[dict] = details if details is not None else []


class BusinessValidationError(AppError):
    code = "BUSINESS_VALIDATION_ERROR"
    status_code = 422


class AuthenticationError(AppError):
    code = "AUTHENTICATION_ERROR"
    status_code = 401


class NotFoundError(AppError):
    code = "NOT_FOUND"
    status_code = 404


class ConflictError(AppError):
    code = "CONFLICT"
    status_code = 409


class ExtractionError(AppError):
    code = "EXTRACTION_FAILED"
    status_code = 422


class RateLimitError(AppError):
    code = "RATE_LIMIT_EXCEEDED"
    status_code = 429


class DatabaseError(AppError):
    code = "INTERNAL_ERROR"
    status_code = 500


def register_error_handlers(app: Flask) -> None:
    """Register centralized JSON error handlers on *app*."""

    @app.errorhandler(AppError)
    def handle_app_error(e: AppError):
        return (
            jsonify(error={"code": e.code, "message": e.message, "details": e.details}),
            e.status_code,
        )

    @app.errorhandler(RequestEntityTooLarge)
    def handle_too_large(e: RequestEntityTooLarge):
        return (
            jsonify(
                error={
                    "code": "FILE_TOO_LARGE",
                    "message": "Upload exceeds the maximum allowed size",
                    "details": [],
                }
            ),
            413,
        )

    @app.errorhandler(Exception)
    def handle_unexpected(e: Exception):
        logger.critical("Unhandled exception", exc_info=e)
        return (
            jsonify(
                error={
                    "code": "INTERNAL_ERROR",
                    "message": "An unexpected error occurred",
                    "details": [],
                }
            ),
            500,
        )
