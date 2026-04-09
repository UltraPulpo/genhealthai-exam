"""Shared test fixtures for the GenHealth AI test suite."""

import pytest

from app import create_app
from app.extensions import db as _db


@pytest.fixture(autouse=True)
def _reset_factories():
    """Reset factory counters between tests."""
    from tests import factories

    for attr in dir(factories):
        cls = getattr(factories, attr)
        if isinstance(cls, type) and hasattr(cls, "_counter"):
            cls._counter = 0


@pytest.fixture()
def app():
    """Create app with TestingConfig and an in-memory database."""
    from app.extensions import smorest_api

    app = create_app("testing")
    app.config["RATELIMIT_ENABLED"] = False
    with app.app_context():
        _db.create_all()
        yield app
        _db.session.rollback()
        _db.drop_all()
    # Reset singleton so test_extensions purity checks still pass
    if hasattr(smorest_api, "_app"):
        smorest_api._app = None


@pytest.fixture()
def client(app):
    """Flask test client."""
    return app.test_client()


@pytest.fixture()
def db_session(app):
    """Database session scoped to the test."""
    return _db.session


@pytest.fixture()
def auth_headers(client, db_session):
    """Register a user via factory and return JWT auth headers."""
    from tests.factories import UserFactory

    user = UserFactory.create(db_session)
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": user.email, "password": "Password1"},
    )
    data = resp.get_json()
    access_token = data["access_token"]
    return {"Authorization": f"Bearer {access_token}"}
