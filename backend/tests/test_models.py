"""Tests for ORM models (Task 3.1)."""

import uuid
from datetime import UTC, datetime

import pytest

from app.models import ActivityLog, Document, Order, OrderStatus, RefreshToken, User


# Uses shared `app` and `db_session` fixtures from conftest.py.
# Alias db_session → session for all existing tests.
@pytest.fixture()
def session(db_session):
    return db_session


# ---------------------------------------------------------------------------
# Import smoke test
# ---------------------------------------------------------------------------


class TestImports:
    """All models can be imported from app.models."""

    def test_import_user(self):
        assert User is not None

    def test_import_order(self):
        assert Order is not None

    def test_import_order_status(self):
        assert OrderStatus is not None

    def test_import_document(self):
        assert Document is not None

    def test_import_activity_log(self):
        assert ActivityLog is not None

    def test_import_refresh_token(self):
        assert RefreshToken is not None


# ---------------------------------------------------------------------------
# OrderStatus enum
# ---------------------------------------------------------------------------


class TestOrderStatus:
    """OrderStatus enum has exactly four values."""

    def test_has_pending(self):
        assert OrderStatus.PENDING.value == "pending"

    def test_has_processing(self):
        assert OrderStatus.PROCESSING.value == "processing"

    def test_has_completed(self):
        assert OrderStatus.COMPLETED.value == "completed"

    def test_has_failed(self):
        assert OrderStatus.FAILED.value == "failed"

    def test_exactly_four_members(self):
        assert len(OrderStatus) == 4


# ---------------------------------------------------------------------------
# User model
# ---------------------------------------------------------------------------


class TestUserModel:
    """User password hashing and verification."""

    def test_set_password_hashes(self, session):
        user = User(email="a@b.com", first_name="A", last_name="B")
        user.set_password("secret123")
        assert user.password_hash is not None
        assert user.password_hash != "secret123"

    def test_check_password_correct(self, session):
        user = User(email="a@b.com", first_name="A", last_name="B")
        user.set_password("secret123")
        assert user.check_password("secret123") is True

    def test_check_password_wrong(self, session):
        user = User(email="a@b.com", first_name="A", last_name="B")
        user.set_password("secret123")
        assert user.check_password("wrong") is False

    def test_id_defaults_to_uuid(self, session):
        user = User(email="x@y.com", first_name="X", last_name="Y")
        user.set_password("pw")
        session.add(user)
        session.flush()
        # Should be a valid UUID string
        uuid.UUID(user.id)

    def test_created_at_defaults(self, session):
        user = User(email="x@y.com", first_name="X", last_name="Y")
        user.set_password("pw")
        session.add(user)
        session.flush()
        assert isinstance(user.created_at, datetime)

    def test_email_unique_constraint(self, session):
        u1 = User(email="dup@test.com", first_name="A", last_name="B")
        u1.set_password("pw")
        u2 = User(email="dup@test.com", first_name="C", last_name="D")
        u2.set_password("pw")
        session.add(u1)
        session.flush()
        session.add(u2)
        with pytest.raises(Exception):  # noqa: B017
            session.flush()


# ---------------------------------------------------------------------------
# Order model
# ---------------------------------------------------------------------------


class TestOrderModel:
    """Order defaults and relationships."""

    def test_default_status_is_pending(self, session):
        user = User(email="o@o.com", first_name="O", last_name="O")
        user.set_password("pw")
        session.add(user)
        session.flush()

        order = Order(created_by=user.id)
        session.add(order)
        session.flush()
        assert order.status == OrderStatus.PENDING.value

    def test_order_has_creator_relationship(self, session):
        user = User(email="r@r.com", first_name="R", last_name="R")
        user.set_password("pw")
        session.add(user)
        session.flush()

        order = Order(created_by=user.id)
        session.add(order)
        session.flush()
        assert order.creator.id == user.id

    def test_order_appears_in_user_orders(self, session):
        user = User(email="u@u.com", first_name="U", last_name="U")
        user.set_password("pw")
        session.add(user)
        session.flush()

        order = Order(created_by=user.id)
        session.add(order)
        session.flush()
        assert order in user.orders


# ---------------------------------------------------------------------------
# Document model
# ---------------------------------------------------------------------------


class TestDocumentModel:
    """Document creation and relationship to Order."""

    def test_document_linked_to_order(self, session):
        user = User(email="d@d.com", first_name="D", last_name="D")
        user.set_password("pw")
        session.add(user)
        session.flush()

        order = Order(created_by=user.id)
        session.add(order)
        session.flush()

        doc = Document(
            order_id=order.id,
            original_filename="test.pdf",
            stored_path="/uploads/test.pdf",
            content_type="application/pdf",
            file_size_bytes=1024,
        )
        session.add(doc)
        session.flush()
        assert doc.order.id == order.id
        assert order.document.id == doc.id


# ---------------------------------------------------------------------------
# ActivityLog model
# ---------------------------------------------------------------------------


class TestActivityLogModel:
    """ActivityLog creation."""

    def test_activity_log_defaults(self, session):
        log = ActivityLog(
            endpoint="/api/health",
            http_method="GET",
            status_code=200,
            ip_address="127.0.0.1",
        )
        session.add(log)
        session.flush()
        assert isinstance(log.timestamp, datetime)
        assert log.user_id is None

    def test_activity_log_with_user(self, session):
        user = User(email="log@t.com", first_name="L", last_name="T")
        user.set_password("pw")
        session.add(user)
        session.flush()

        log = ActivityLog(
            user_id=user.id,
            endpoint="/api/orders",
            http_method="POST",
            status_code=201,
            ip_address="10.0.0.1",
        )
        session.add(log)
        session.flush()
        assert log.user_id == user.id


# ---------------------------------------------------------------------------
# RefreshToken model
# ---------------------------------------------------------------------------


class TestRefreshTokenModel:
    """RefreshToken creation."""

    def test_refresh_token_creation(self, session):
        user = User(email="rt@t.com", first_name="R", last_name="T")
        user.set_password("pw")
        session.add(user)
        session.flush()

        token = RefreshToken(
            user_id=user.id,
            token_hash="abc123hash",
            expires_at=datetime(2099, 1, 1, tzinfo=UTC),
        )
        session.add(token)
        session.flush()
        assert token.user_id == user.id
        assert isinstance(token.created_at, datetime)

    def test_refresh_token_in_user_relationship(self, session):
        user = User(email="rt2@t.com", first_name="R", last_name="T")
        user.set_password("pw")
        session.add(user)
        session.flush()

        token = RefreshToken(
            user_id=user.id,
            token_hash="xyz789hash",
            expires_at=datetime(2099, 1, 1, tzinfo=UTC),
        )
        session.add(token)
        session.flush()
        assert token in user.refresh_tokens


# ---------------------------------------------------------------------------
# Relationship definitions
# ---------------------------------------------------------------------------


class TestRelationships:
    """Model relationships are properly defined."""

    def test_user_has_orders_relationship(self):
        assert hasattr(User, "orders")

    def test_user_has_activity_logs_relationship(self):
        assert hasattr(User, "activity_logs")

    def test_user_has_refresh_tokens_relationship(self):
        assert hasattr(User, "refresh_tokens")

    def test_order_has_creator_relationship(self):
        assert hasattr(Order, "creator")

    def test_order_has_document_relationship(self):
        assert hasattr(Order, "document")

    def test_document_has_order_relationship(self):
        assert hasattr(Document, "order")
