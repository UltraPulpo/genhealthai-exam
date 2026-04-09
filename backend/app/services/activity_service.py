"""Activity service."""

from app.repositories import ActivityLogRepository


class ActivityService:
    def __init__(self, log_repo: ActivityLogRepository):
        self.log_repo = log_repo

    def list_logs(self, page: int, per_page: int, filters: dict) -> tuple[list, int]:
        return self.log_repo.list_paginated(page, per_page, filters)
