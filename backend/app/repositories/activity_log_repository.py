"""Activity-log repository."""

import logging

from sqlalchemy import func, select

from app.models.activity_log import ActivityLog
from app.repositories.base_repository import BaseRepository

logger = logging.getLogger(__name__)


class ActivityLogRepository(BaseRepository):
    model_class = ActivityLog

    def log_request(
        self,
        user_id: str | None,
        endpoint: str,
        method: str,
        status_code: int,
        ip: str,
        user_agent: str,
    ) -> ActivityLog | None:
        """Create a log entry inside a savepoint so failures don't affect the caller."""
        try:
            nested = self.session.begin_nested()
            log = ActivityLog(
                user_id=user_id,
                endpoint=endpoint,
                http_method=method,
                status_code=status_code,
                ip_address=ip,
                user_agent=user_agent,
            )
            self.session.add(log)
            nested.commit()
            return log
        except Exception:
            logger.exception("Failed to write activity log")
            return None

    def list_paginated(
        self, page: int, per_page: int, filters: dict | None = None
    ) -> tuple[list[ActivityLog], int]:
        """Return ``(items, total_count)`` with optional filters."""
        filters = filters or {}

        stmt = select(ActivityLog)
        count_stmt = select(func.count()).select_from(ActivityLog)

        if "user_id" in filters:
            stmt = stmt.where(ActivityLog.user_id == filters["user_id"])
            count_stmt = count_stmt.where(ActivityLog.user_id == filters["user_id"])

        if "endpoint" in filters:
            stmt = stmt.where(ActivityLog.endpoint == filters["endpoint"])
            count_stmt = count_stmt.where(ActivityLog.endpoint == filters["endpoint"])

        if "method" in filters:
            stmt = stmt.where(ActivityLog.http_method == filters["method"])
            count_stmt = count_stmt.where(ActivityLog.http_method == filters["method"])

        if "status_code" in filters:
            stmt = stmt.where(ActivityLog.status_code == filters["status_code"])
            count_stmt = count_stmt.where(ActivityLog.status_code == filters["status_code"])

        if "date_from" in filters:
            stmt = stmt.where(ActivityLog.timestamp >= filters["date_from"])
            count_stmt = count_stmt.where(ActivityLog.timestamp >= filters["date_from"])

        if "date_to" in filters:
            stmt = stmt.where(ActivityLog.timestamp <= filters["date_to"])
            count_stmt = count_stmt.where(ActivityLog.timestamp <= filters["date_to"])

        stmt = stmt.order_by(ActivityLog.timestamp.desc())
        offset = (page - 1) * per_page
        stmt = stmt.offset(offset).limit(per_page)

        items = self.session.execute(stmt).scalars().all()
        total = self.session.execute(count_stmt).scalar()
        return list(items), total
