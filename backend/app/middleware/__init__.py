"""Application middleware registration."""

from app.middleware.logging_middleware import logging_after_request


def register_middleware(app):
    """Register all application middleware."""
    app.after_request(logging_after_request)
