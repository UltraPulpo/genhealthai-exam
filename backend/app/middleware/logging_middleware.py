"""Activity logging after-request hook."""

import logging

from flask import request
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request

from app.extensions import db
from app.repositories import ActivityLogRepository

logger = logging.getLogger(__name__)


def logging_after_request(response):
    """After-request hook: log every request to the activity log table.

    Extracts JWT identity when present (unauthenticated requests are logged
    with user_id=None). The repository uses a savepoint internally, so logging
    failures can never roll back the main transaction. The outer try/except is
    an additional safety net to ensure the original response is always returned.
    """
    try:
        user_id = None
        try:
            # optional=True prevents an error when no JWT is present
            verify_jwt_in_request(optional=True)
            user_id = get_jwt_identity()
        except Exception:
            pass  # Unauthenticated request — log with user_id=None

        repo = ActivityLogRepository(db.session)
        repo.log_request(
            user_id=user_id,
            endpoint=request.path,
            method=request.method,
            status_code=response.status_code,
            ip=request.remote_addr,
            user_agent=request.headers.get("User-Agent", ""),
        )
    except Exception:
        logger.exception("Activity logging failed")

    return response
