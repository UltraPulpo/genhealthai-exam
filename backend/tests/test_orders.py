"""Order service and route tests."""

import os
from unittest.mock import patch

import pytest

from app.repositories import DocumentRepository, OrderRepository
from app.services import OrderService
from app.utils.errors import NotFoundError
from tests.factories import DocumentFactory, OrderFactory, UserFactory


# ── Helpers ──────────────────────────────────────────────────────────


def _order_service(session):
    return OrderService(
        order_repo=OrderRepository(session),
        doc_repo=DocumentRepository(session),
    )


# ── Service-level tests ────────────────────────────────────────────


class TestOrderServiceCreate:
    def test_create_order(self, db_session):
        user = UserFactory.create(db_session)
        svc = _order_service(db_session)
        order = svc.create_order(
            user.id,
            {
                "patient_first_name": "Jane",
                "patient_last_name": "Smith",
                "equipment_type": "CPAP",
            },
        )
        assert order.id is not None
        assert order.created_by == user.id
        assert order.status == "pending"
        assert order.patient_first_name == "Jane"


class TestOrderServiceGet:
    def test_get_order_found(self, db_session):
        user = UserFactory.create(db_session)
        order = OrderFactory.create(db_session, created_by=user.id)
        svc = _order_service(db_session)
        result = svc.get_order(order.id)
        assert result.id == order.id

    def test_get_order_not_found(self, db_session):
        svc = _order_service(db_session)
        with pytest.raises(NotFoundError):
            svc.get_order("nonexistent-id")


class TestOrderServiceUpdate:
    def test_update_order(self, db_session):
        user = UserFactory.create(db_session)
        order = OrderFactory.create(db_session, created_by=user.id)
        svc = _order_service(db_session)
        updated = svc.update_order(order.id, {"patient_first_name": "Updated"})
        assert updated.patient_first_name == "Updated"

    def test_update_order_immutable_fields(self, db_session):
        user = UserFactory.create(db_session)
        order = OrderFactory.create(db_session, created_by=user.id)
        original_id = order.id
        original_creator = order.created_by
        svc = _order_service(db_session)
        svc.update_order(order.id, {"id": "hacked", "created_by": "hacked"})
        assert order.id == original_id
        assert order.created_by == original_creator


class TestOrderServiceDelete:
    def test_delete_order_with_document(self, db_session, app):
        user = UserFactory.create(db_session)
        order = OrderFactory.create(db_session, created_by=user.id)
        stored_path = os.path.join(app.config["UPLOAD_FOLDER"], "to_delete.pdf")
        os.makedirs(os.path.dirname(stored_path), exist_ok=True)
        try:
            with open(stored_path, "wb") as f:
                f.write(b"fake pdf")
            DocumentFactory.create(
                db_session, order_id=order.id, stored_path=stored_path
            )
            svc = _order_service(db_session)
            svc.delete_order(order.id)
            assert OrderRepository(db_session).get_by_id(order.id) is None
            assert not os.path.exists(stored_path)
        finally:
            if os.path.exists(stored_path):
                os.remove(stored_path)

    def test_delete_order_without_document(self, db_session):
        user = UserFactory.create(db_session)
        order = OrderFactory.create(db_session, created_by=user.id)
        svc = _order_service(db_session)
        svc.delete_order(order.id)
        assert OrderRepository(db_session).get_by_id(order.id) is None

    def test_delete_order_file_missing(self, db_session):
        user = UserFactory.create(db_session)
        order = OrderFactory.create(db_session, created_by=user.id)
        DocumentFactory.create(
            db_session,
            order_id=order.id,
            stored_path="/nonexistent/path/file.pdf",
        )
        svc = _order_service(db_session)
        # Should not raise even if file is missing
        svc.delete_order(order.id)
        assert OrderRepository(db_session).get_by_id(order.id) is None


# ── Integration (API) tests ────────────────────────────────────────


class TestCreateOrderAPI:
    def test_create_order_api(self, client, auth_headers):
        resp = client.post(
            "/api/v1/orders/",
            json={
                "patient_first_name": "API",
                "patient_last_name": "User",
                "equipment_type": "Walker",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["patient_first_name"] == "API"
        assert data["status"] == "pending"


class TestListOrdersAPI:
    def test_list_orders_pagination(self, client, auth_headers, db_session):
        # Orders created under a different user; endpoint returns all orders (no ownership filter)
        user = UserFactory.create(db_session, email="lister@test.com")
        for _ in range(5):
            OrderFactory.create(db_session, created_by=user.id)
        resp = client.get(
            "/api/v1/orders/?page=1&per_page=2", headers=auth_headers
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data["data"]) == 2
        assert data["pagination"]["total"] == 5

    def test_list_orders_filter_status(self, client, auth_headers, db_session):
        user = UserFactory.create(db_session, email="filter_s@test.com")
        OrderFactory.create(db_session, created_by=user.id, status="completed")
        OrderFactory.create(db_session, created_by=user.id, status="pending")
        resp = client.get(
            "/api/v1/orders/?status=completed", headers=auth_headers
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["pagination"]["total"] == 1
        assert data["data"][0]["status"] == "completed"


class TestGetOrderAPI:
    def test_get_order_by_id(self, client, auth_headers, db_session):
        user = UserFactory.create(db_session, email="getter@test.com")
        order = OrderFactory.create(db_session, created_by=user.id)
        resp = client.get(f"/api/v1/orders/{order.id}", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.get_json()["id"] == order.id

    def test_get_order_not_found_api(self, client, auth_headers):
        resp = client.get("/api/v1/orders/nonexistent-id", headers=auth_headers)
        assert resp.status_code == 404


class TestUpdateOrderAPI:
    def test_update_order_api(self, client, auth_headers, db_session):
        user = UserFactory.create(db_session, email="updater@test.com")
        order = OrderFactory.create(db_session, created_by=user.id)
        resp = client.put(
            f"/api/v1/orders/{order.id}",
            json={"patient_first_name": "Updated"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.get_json()["patient_first_name"] == "Updated"

    def test_update_order_immutable_fields_api(
        self, client, auth_headers, db_session
    ):
        user = UserFactory.create(db_session, email="immutable@test.com")
        order = OrderFactory.create(db_session, created_by=user.id)
        resp = client.put(
            f"/api/v1/orders/{order.id}",
            json={"patient_first_name": "Changed"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.get_json()["created_by"] == user.id


class TestDeleteOrderAPI:
    def test_delete_order_api(self, client, auth_headers, db_session):
        user = UserFactory.create(db_session, email="deleter@test.com")
        order = OrderFactory.create(db_session, created_by=user.id)
        resp = client.delete(
            f"/api/v1/orders/{order.id}", headers=auth_headers
        )
        assert resp.status_code == 204
        resp2 = client.get(
            f"/api/v1/orders/{order.id}", headers=auth_headers
        )
        assert resp2.status_code == 404
