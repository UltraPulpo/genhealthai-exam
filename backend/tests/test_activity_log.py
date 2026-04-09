"""Activity log middleware and admin route tests."""

import pytest

from tests.factories import UserFactory


class TestActivityLogMiddleware:
    def test_activity_log_created_on_request(self, client, db_session, app):
        """Every request should create an activity log entry."""
        from app.models import ActivityLog
        from sqlalchemy import select

        initial = db_session.execute(select(ActivityLog)).scalars().all()
        client.get("/api/v1/health")
        logs = db_session.execute(select(ActivityLog)).scalars().all()
        assert len(logs) > len(initial)

    def test_activity_log_unauthenticated(self, client, db_session):
        """Unauthenticated requests should log with user_id=None."""
        from app.models import ActivityLog
        from sqlalchemy import select

        client.get("/api/v1/health")
        logs = db_session.execute(
            select(ActivityLog).where(ActivityLog.endpoint == "/api/v1/health")
        ).scalars().all()
        assert len(logs) >= 1
        assert logs[0].user_id is None


class TestActivityLogAdminAPI:
    def test_list_activity_logs(self, client, auth_headers, db_session):
        # Make a few requests to generate logs
        client.get("/api/v1/health")
        client.get("/api/v1/health")
        resp = client.get(
            "/api/v1/admin/activity-logs", headers=auth_headers
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert "data" in data
        assert "pagination" in data
        assert data["pagination"]["total"] >= 2

    def test_list_activity_logs_filter(self, client, auth_headers, db_session):
        client.get("/api/v1/health")
        resp = client.get(
            "/api/v1/admin/activity-logs?endpoint=/api/v1/health",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.get_json()
        for item in data["data"]:
            assert item["endpoint"] == "/api/v1/health"
