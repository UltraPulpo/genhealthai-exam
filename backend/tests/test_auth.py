"""Auth service and route tests."""

import pytest

from app.extensions import db
from app.repositories import RefreshTokenRepository, UserRepository
from app.services import AuthService
from app.utils.errors import AuthenticationError, BusinessValidationError, ConflictError
from tests.factories import UserFactory


# ── Helpers ──────────────────────────────────────────────────────────


def _auth_service(session):
    return AuthService(
        user_repo=UserRepository(session),
        token_repo=RefreshTokenRepository(session),
    )


# ── Service-level tests ────────────────────────────────────────────


class TestAuthServiceRegister:
    def test_register_success(self, db_session):
        svc = _auth_service(db_session)
        user = svc.register("new@test.com", "Password1", "New", "User")
        assert user.email == "new@test.com"
        assert user.check_password("Password1")

    def test_register_duplicate_email(self, db_session):
        svc = _auth_service(db_session)
        svc.register("dup@test.com", "Password1", "A", "B")
        with pytest.raises(ConflictError):
            svc.register("dup@test.com", "Password1", "C", "D")

    def test_register_weak_password(self, db_session):
        svc = _auth_service(db_session)
        with pytest.raises(BusinessValidationError):
            svc.register("weak@test.com", "short", "A", "B")


class TestAuthServiceLogin:
    def test_login_success(self, db_session):
        UserFactory.create(db_session, email="login@test.com")
        svc = _auth_service(db_session)
        access, refresh = svc.login("login@test.com", "Password1")
        assert access
        assert refresh

    def test_login_wrong_password(self, db_session):
        UserFactory.create(db_session, email="wrong@test.com")
        svc = _auth_service(db_session)
        with pytest.raises(AuthenticationError):
            svc.login("wrong@test.com", "BadPassword1")

    def test_login_unknown_email(self, db_session):
        svc = _auth_service(db_session)
        with pytest.raises(AuthenticationError):
            svc.login("nobody@test.com", "Password1")


class TestAuthServiceRefresh:
    def test_refresh_success(self, db_session):
        UserFactory.create(db_session, email="ref@test.com")
        svc = _auth_service(db_session)
        _, raw_refresh = svc.login("ref@test.com", "Password1")
        new_access, new_refresh = svc.refresh(raw_refresh)
        assert new_access
        assert new_refresh
        assert new_refresh != raw_refresh

    def test_refresh_invalid_token(self, db_session):
        svc = _auth_service(db_session)
        with pytest.raises(AuthenticationError):
            svc.refresh("completely-invalid-token")

    def test_refresh_expired_token(self, db_session):
        import hashlib
        from datetime import datetime, timedelta, timezone

        user = UserFactory.create(db_session, email="exp@test.com")
        repo = RefreshTokenRepository(db_session)
        raw = "expired-raw-token"
        token_hash = hashlib.sha256(raw.encode()).hexdigest()
        repo.create_token(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=datetime.now(timezone.utc).replace(tzinfo=None)
            - timedelta(hours=1),
        )
        repo.commit()
        svc = _auth_service(db_session)
        with pytest.raises(AuthenticationError):
            svc.refresh(raw)


class TestAuthServiceLogout:
    def test_logout_revokes_all_tokens(self, db_session):
        user = UserFactory.create(db_session, email="logout@test.com")
        svc = _auth_service(db_session)
        svc.login("logout@test.com", "Password1")
        svc.login("logout@test.com", "Password1")
        svc.logout(user.id)
        repo = RefreshTokenRepository(db_session)
        # All tokens should be gone
        from app.models import RefreshToken
        from sqlalchemy import select

        count = db_session.execute(
            select(RefreshToken).where(RefreshToken.user_id == user.id)
        ).scalars().all()
        assert len(count) == 0


# ── Integration (API) tests ────────────────────────────────────────


class TestRegisterAPI:
    def test_register_and_login_flow(self, client):
        resp = client.post(
            "/api/v1/auth/register",
            json={
                "email": "flow@test.com",
                "password": "Password1",
                "first_name": "Flow",
                "last_name": "Test",
            },
        )
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["email"] == "flow@test.com"

        resp2 = client.post(
            "/api/v1/auth/login",
            json={"email": "flow@test.com", "password": "Password1"},
        )
        assert resp2.status_code == 200
        tokens = resp2.get_json()
        assert "access_token" in tokens
        assert "refresh_token" in tokens

    def test_register_duplicate_email_api(self, client):
        payload = {
            "email": "dup2@test.com",
            "password": "Password1",
            "first_name": "A",
            "last_name": "B",
        }
        client.post("/api/v1/auth/register", json=payload)
        resp = client.post("/api/v1/auth/register", json=payload)
        assert resp.status_code == 409

    def test_register_validation_errors(self, client):
        resp = client.post(
            "/api/v1/auth/register",
            json={"email": "bad-email", "password": "x", "first_name": "A", "last_name": "B"},
        )
        assert resp.status_code == 422


class TestLoginAPI:
    def test_login_invalid_credentials(self, client, db_session):
        UserFactory.create(db_session, email="api_login@test.com")
        resp = client.post(
            "/api/v1/auth/login",
            json={"email": "api_login@test.com", "password": "WrongPassword1"},
        )
        assert resp.status_code == 401


class TestRefreshAPI:
    def test_token_refresh_flow(self, client, db_session):
        UserFactory.create(db_session, email="refresh_api@test.com")
        login_resp = client.post(
            "/api/v1/auth/login",
            json={"email": "refresh_api@test.com", "password": "Password1"},
        )
        tokens = login_resp.get_json()
        refresh_resp = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": tokens["refresh_token"]},
        )
        assert refresh_resp.status_code == 200
        new_tokens = refresh_resp.get_json()
        assert "access_token" in new_tokens
        assert "refresh_token" in new_tokens

    def test_token_refresh_invalidates_old_token(self, client, db_session):
        UserFactory.create(db_session, email="invalidate@test.com")
        login_resp = client.post(
            "/api/v1/auth/login",
            json={"email": "invalidate@test.com", "password": "Password1"},
        )
        old_refresh = login_resp.get_json()["refresh_token"]
        client.post("/api/v1/auth/refresh", json={"refresh_token": old_refresh})
        # Old token should no longer work
        resp = client.post(
            "/api/v1/auth/refresh", json={"refresh_token": old_refresh}
        )
        assert resp.status_code == 401

    def test_token_refresh_expired(self, client):
        resp = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "nonexistent-token"},
        )
        assert resp.status_code == 401


class TestLogoutAPI:
    def test_logout_revokes_tokens(self, client, db_session):
        UserFactory.create(db_session, email="logout_api@test.com")
        login_resp = client.post(
            "/api/v1/auth/login",
            json={"email": "logout_api@test.com", "password": "Password1"},
        )
        tokens = login_resp.get_json()
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}
        resp = client.post("/api/v1/auth/logout", headers=headers)
        assert resp.status_code == 204
        # Refresh token should be invalid now
        resp2 = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": tokens["refresh_token"]},
        )
        assert resp2.status_code == 401


class TestProtectedRoutes:
    def test_protected_route_no_token(self, client):
        resp = client.get("/api/v1/auth/me")
        assert resp.status_code == 401

    def test_get_current_user(self, client, auth_headers):
        resp = client.get("/api/v1/auth/me", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert "email" in data

    def test_protected_route_expired_token(self, client, app):
        from datetime import timedelta

        app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(seconds=-1)
        from flask_jwt_extended import create_access_token

        with app.app_context():
            token = create_access_token(identity="fake-user-id")
        headers = {"Authorization": f"Bearer {token}"}
        resp = client.get("/api/v1/auth/me", headers=headers)
        assert resp.status_code == 401
