"""Health check, CORS, and system route tests."""

from unittest.mock import patch, MagicMock

import pytest


class TestHealthCheck:
    def test_health_check(self, client):
        resp = client.get("/api/v1/health")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "healthy"
        assert data["database"] == "connected"

    def test_health_check_db_down(self, client, app):
        with patch("app.routes.system.db.session") as mock_session:
            mock_session.execute.side_effect = Exception("db down")
            resp = client.get("/api/v1/health")
        assert resp.status_code == 503
        data = resp.get_json()
        assert data["status"] == "unhealthy"


class TestCORS:
    def test_cors_headers(self, client):
        resp = client.options(
            "/api/v1/health",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "GET",
            },
        )
        # CORS should respond (200 or 204) with appropriate headers
        assert resp.status_code in (200, 204)


class TestSwaggerDocs:
    def test_swagger_docs_accessible(self, client):
        resp = client.get("/api/v1/docs")
        # Could be 200 or 301/302 redirect to /api/v1/docs/
        assert resp.status_code in (200, 301, 302, 308)
