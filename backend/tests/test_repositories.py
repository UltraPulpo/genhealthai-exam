"""Tests for all repository classes."""

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from flask import Flask

from app.extensions import db as _db
from app.models import (
    ActivityLog,
    Document,
    Order,
    OrderStatus,
    RefreshToken,
    User,
)
from app.repositories import (
    ActivityLogRepository,
    DocumentRepository,
    OrderRepository,
    RefreshTokenRepository,
    UserRepository,
)


# ── Fixtures ────────────────────────────────────────────────────────


@pytest.fixture
def app():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["TESTING"] = True
    _db.init_app(app)
    with app.app_context():
        _db.create_all()
        yield app
        _db.drop_all()


@pytest.fixture
def session(app):
    with app.app_context():
        yield _db.session


def _make_user(session, **overrides):
    attrs = {
        "id": str(uuid.uuid4()),
        "email": f"{uuid.uuid4().hex[:8]}@example.com",
        "password_hash": "fakehash",
        "first_name": "Test",
        "last_name": "User",
    }
    attrs.update(overrides)
    user = User(**attrs)
    session.add(user)
    session.flush()
    return user


def _make_order(session, user_id, **overrides):
    attrs = {
        "id": str(uuid.uuid4()),
        "created_by": user_id,
        "status": OrderStatus.PENDING.value,
    }
    attrs.update(overrides)
    order = Order(**attrs)
    session.add(order)
    session.flush()
    return order


def _make_document(session, order_id, **overrides):
    attrs = {
        "id": str(uuid.uuid4()),
        "order_id": order_id,
        "original_filename": "test.pdf",
        "stored_path": "/uploads/test.pdf",
        "content_type": "application/pdf",
        "file_size_bytes": 1024,
    }
    attrs.update(overrides)
    doc = Document(**attrs)
    session.add(doc)
    session.flush()
    return doc


# ── UserRepository ──────────────────────────────────────────────────


class TestUserRepository:
    def test_get_by_email_found(self, session):
        user = _make_user(session, email="alice@example.com")
        repo = UserRepository(session)

        result = repo.get_by_email("alice@example.com")

        assert result is not None
        assert result.id == user.id

    def test_get_by_email_not_found(self, session):
        repo = UserRepository(session)

        assert repo.get_by_email("nobody@example.com") is None

    def test_get_by_email_case_insensitive(self, session):
        user = _make_user(session, email="Bob@Example.COM")
        repo = UserRepository(session)

        result = repo.get_by_email("bob@example.com")

        assert result is not None
        assert result.id == user.id

    def test_email_exists_true(self, session):
        _make_user(session, email="exists@example.com")
        repo = UserRepository(session)

        assert repo.email_exists("exists@example.com") is True

    def test_email_exists_false(self, session):
        repo = UserRepository(session)

        assert repo.email_exists("ghost@example.com") is False


# ── OrderRepository ─────────────────────────────────────────────────


class TestOrderRepository:
    def test_list_paginated_basic(self, session):
        user = _make_user(session)
        for _ in range(5):
            _make_order(session, user.id)
        repo = OrderRepository(session)

        items, total = repo.list_paginated(page=1, per_page=2)

        assert len(items) == 2
        assert total == 5

    def test_list_paginated_filter_status(self, session):
        user = _make_user(session)
        _make_order(session, user.id, status=OrderStatus.COMPLETED.value)
        _make_order(session, user.id, status=OrderStatus.PENDING.value)
        _make_order(session, user.id, status=OrderStatus.COMPLETED.value)
        repo = OrderRepository(session)

        items, total = repo.list_paginated(
            page=1, per_page=10, filters={"status": OrderStatus.COMPLETED.value}
        )

        assert total == 2
        assert all(o.status == OrderStatus.COMPLETED.value for o in items)

    def test_list_paginated_filter_patient_name(self, session):
        user = _make_user(session)
        _make_order(session, user.id, patient_last_name="Johnson")
        _make_order(session, user.id, patient_last_name="Smith")
        _make_order(session, user.id, patient_last_name="Johnston")
        repo = OrderRepository(session)

        items, total = repo.list_paginated(
            page=1, per_page=10, filters={"patient_last_name": "John"}
        )

        assert total == 2
        assert all("John" in o.patient_last_name for o in items)

    def test_list_paginated_filter_date_range(self, session):
        user = _make_user(session)
        now = datetime.now(UTC)
        old = now - timedelta(days=10)
        recent = now - timedelta(hours=1)

        o1 = _make_order(session, user.id)
        o2 = _make_order(session, user.id)
        # Manually set created_at
        o1.created_at = old
        o2.created_at = recent
        session.flush()

        repo = OrderRepository(session)
        items, total = repo.list_paginated(
            page=1,
            per_page=10,
            filters={
                "created_after": now - timedelta(days=1),
                "created_before": now + timedelta(hours=1),
            },
        )

        assert total == 1
        assert items[0].id == o2.id

    def test_list_paginated_sorting(self, session):
        user = _make_user(session)
        _make_order(session, user.id, patient_last_name="Charlie")
        _make_order(session, user.id, patient_last_name="Alice")
        _make_order(session, user.id, patient_last_name="Bob")
        repo = OrderRepository(session)

        items, _ = repo.list_paginated(
            page=1,
            per_page=10,
            filters={"sort_by": "patient_last_name", "sort_order": "asc"},
        )

        names = [o.patient_last_name for o in items]
        assert names == ["Alice", "Bob", "Charlie"]

    def test_get_with_document_has_doc(self, session):
        user = _make_user(session)
        order = _make_order(session, user.id)
        doc = _make_document(session, order.id)
        session.commit()

        repo = OrderRepository(session)
        result = repo.get_with_document(order.id)

        assert result is not None
        assert result.document is not None
        assert result.document.id == doc.id

    def test_get_with_document_no_doc(self, session):
        user = _make_user(session)
        order = _make_order(session, user.id)
        session.commit()

        repo = OrderRepository(session)
        result = repo.get_with_document(order.id)

        assert result is not None
        assert result.document is None


# ── DocumentRepository ──────────────────────────────────────────────


class TestDocumentRepository:
    def test_get_by_order_id(self, session):
        user = _make_user(session)
        order = _make_order(session, user.id)
        doc = _make_document(session, order.id)
        repo = DocumentRepository(session)

        result = repo.get_by_order_id(order.id)

        assert result is not None
        assert result.id == doc.id

    def test_get_by_order_id_not_found(self, session):
        repo = DocumentRepository(session)

        assert repo.get_by_order_id("nonexistent-id") is None

    def test_delete_by_order_id(self, session):
        user = _make_user(session)
        order = _make_order(session, user.id)
        _make_document(session, order.id)
        repo = DocumentRepository(session)

        repo.delete_by_order_id(order.id)
        session.flush()

        assert repo.get_by_order_id(order.id) is None


# ── RefreshTokenRepository ──────────────────────────────────────────


class TestRefreshTokenRepository:
    def test_create_and_find(self, session):
        user = _make_user(session)
        repo = RefreshTokenRepository(session)

        token = repo.create_token(
            user_id=user.id,
            token_hash="abc123",
            expires_at=datetime.now(UTC) + timedelta(days=7),
        )
        session.flush()

        found = repo.find_by_hash("abc123")
        assert found is not None
        assert found.id == token.id

    def test_find_expired_returns_none(self, session):
        user = _make_user(session)
        repo = RefreshTokenRepository(session)

        repo.create_token(
            user_id=user.id,
            token_hash="expired_hash",
            expires_at=datetime.now(UTC) - timedelta(hours=1),
        )
        session.flush()

        assert repo.find_by_hash("expired_hash") is None

    def test_delete_by_hash(self, session):
        user = _make_user(session)
        repo = RefreshTokenRepository(session)

        repo.create_token(
            user_id=user.id,
            token_hash="to_delete",
            expires_at=datetime.now(UTC) + timedelta(days=1),
        )
        session.flush()

        repo.delete_by_hash("to_delete")
        session.flush()

        assert repo.find_by_hash("to_delete") is None

    def test_delete_all_for_user(self, session):
        user = _make_user(session)
        repo = RefreshTokenRepository(session)

        for i in range(3):
            repo.create_token(
                user_id=user.id,
                token_hash=f"token_{i}",
                expires_at=datetime.now(UTC) + timedelta(days=1),
            )
        session.flush()

        repo.delete_all_for_user(user.id)
        session.flush()

        for i in range(3):
            assert repo.find_by_hash(f"token_{i}") is None

    def test_delete_expired(self, session):
        user = _make_user(session)
        repo = RefreshTokenRepository(session)

        # 2 expired
        for i in range(2):
            repo.create_token(
                user_id=user.id,
                token_hash=f"exp_{i}",
                expires_at=datetime.now(UTC) - timedelta(hours=1),
            )
        # 1 valid
        repo.create_token(
            user_id=user.id,
            token_hash="valid",
            expires_at=datetime.now(UTC) + timedelta(days=1),
        )
        session.flush()

        count = repo.delete_expired()
        session.flush()

        assert count == 2
        assert repo.find_by_hash("valid") is not None


# ── ActivityLogRepository ───────────────────────────────────────────


class TestActivityLogRepository:
    def test_log_request(self, session):
        user = _make_user(session)
        repo = ActivityLogRepository(session)

        log = repo.log_request(
            user_id=user.id,
            endpoint="/api/orders",
            method="GET",
            status_code=200,
            ip="127.0.0.1",
            user_agent="TestAgent/1.0",
        )

        assert log is not None
        assert log.endpoint == "/api/orders"
        assert log.http_method == "GET"
        assert log.status_code == 200

    def test_log_request_savepoint_isolation(self, session):
        """Prove that a failed savepoint does not roll back the outer transaction."""
        user = _make_user(session)
        repo = ActivityLogRepository(session)

        # Create an order in the outer transaction
        order = _make_order(session, user.id)
        order_id = order.id

        # Simulate a savepoint failure by patching begin_nested
        original_begin_nested = session.begin_nested

        def _failing_begin_nested():
            nested = original_begin_nested()
            raise RuntimeError("Simulated savepoint failure")

        session.begin_nested = _failing_begin_nested

        result = repo.log_request(
            user_id=user.id,
            endpoint="/fail",
            method="POST",
            status_code=500,
            ip="127.0.0.1",
            user_agent="TestAgent/1.0",
        )

        # Restore original
        session.begin_nested = original_begin_nested

        # Savepoint failed, so log_request returns None
        assert result is None

        # Outer transaction's order should still be accessible
        found = session.get(Order, order_id)
        assert found is not None

    def test_list_paginated_basic(self, session):
        user = _make_user(session)
        repo = ActivityLogRepository(session)

        for _ in range(5):
            repo.log_request(
                user_id=user.id,
                endpoint="/api/test",
                method="GET",
                status_code=200,
                ip="127.0.0.1",
                user_agent="Agent",
            )

        items, total = repo.list_paginated(page=1, per_page=2)

        assert len(items) == 2
        assert total == 5

    def test_list_paginated_filters(self, session):
        user = _make_user(session)
        other_user = _make_user(session)
        repo = ActivityLogRepository(session)

        repo.log_request(user.id, "/api/orders", "GET", 200, "127.0.0.1", "A")
        repo.log_request(user.id, "/api/users", "POST", 201, "127.0.0.1", "A")
        repo.log_request(other_user.id, "/api/orders", "GET", 200, "10.0.0.1", "B")

        # Filter by user_id
        items, total = repo.list_paginated(
            page=1, per_page=10, filters={"user_id": user.id}
        )
        assert total == 2

        # Filter by endpoint
        items, total = repo.list_paginated(
            page=1, per_page=10, filters={"endpoint": "/api/orders"}
        )
        assert total == 2

        # Filter by date range
        now = datetime.now(UTC)
        items, total = repo.list_paginated(
            page=1,
            per_page=10,
            filters={
                "date_from": now - timedelta(minutes=5),
                "date_to": now + timedelta(minutes=5),
            },
        )
        assert total == 3


# ── BaseRepository ──────────────────────────────────────────────────


class TestBaseRepository:
    def test_get_by_id(self, session):
        user = _make_user(session)
        repo = UserRepository(session)

        result = repo.get_by_id(user.id)

        assert result is not None
        assert result.email == user.email

    def test_get_by_id_not_found(self, session):
        repo = UserRepository(session)

        assert repo.get_by_id("nonexistent") is None

    def test_create(self, session):
        repo = UserRepository(session)

        user = repo.create(
            {
                "email": "new@example.com",
                "password_hash": "hash",
                "first_name": "New",
                "last_name": "User",
            }
        )
        session.flush()

        assert user.id is not None
        assert user.email == "new@example.com"

    def test_update(self, session):
        user = _make_user(session, first_name="Old")
        repo = UserRepository(session)

        repo.update(user, {"first_name": "New"})
        session.flush()

        assert user.first_name == "New"

    def test_delete(self, session):
        user = _make_user(session)
        uid = user.id
        repo = UserRepository(session)

        repo.delete(user)
        session.flush()

        assert repo.get_by_id(uid) is None

    def test_commit(self, session):
        repo = UserRepository(session)
        repo.create(
            {
                "email": "commit@example.com",
                "password_hash": "hash",
                "first_name": "C",
                "last_name": "D",
            }
        )
        repo.commit()

        found = repo.get_by_email("commit@example.com")
        assert found is not None
