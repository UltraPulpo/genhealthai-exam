"""Tests for Marshmallow schemas (Task 4.1)."""

from datetime import date, datetime, timezone

import pytest
from marshmallow import ValidationError

from app.schemas import (
    ActivityLogQuerySchema,
    ActivityLogSchema,
    DocumentSchema,
    ErrorSchema,
    LoginSchema,
    OrderCreateSchema,
    OrderQuerySchema,
    OrderResponseSchema,
    OrderUpdateSchema,
    RegisterSchema,
    TokenSchema,
    UserSchema,
)


# ---------------------------------------------------------------------------
# Auth Schemas
# ---------------------------------------------------------------------------


class TestRegisterSchema:
    def test_loads_valid_data(self):
        data = {
            "email": "user@example.com",
            "password": "secret123",
            "first_name": "Jane",
            "last_name": "Doe",
        }
        result = RegisterSchema().load(data)
        assert result["email"] == "user@example.com"
        assert result["password"] == "secret123"
        assert result["first_name"] == "Jane"
        assert result["last_name"] == "Doe"

    @pytest.mark.parametrize("missing_field", ["email", "password", "first_name", "last_name"])
    def test_rejects_missing_required_field(self, missing_field):
        data = {
            "email": "user@example.com",
            "password": "secret123",
            "first_name": "Jane",
            "last_name": "Doe",
        }
        del data[missing_field]
        with pytest.raises(ValidationError) as exc_info:
            RegisterSchema().load(data)
        assert missing_field in exc_info.value.messages

    def test_rejects_invalid_email(self):
        data = {
            "email": "not-an-email",
            "password": "secret123",
            "first_name": "Jane",
            "last_name": "Doe",
        }
        with pytest.raises(ValidationError) as exc_info:
            RegisterSchema().load(data)
        assert "email" in exc_info.value.messages

    def test_password_is_load_only(self):
        data = {
            "email": "user@example.com",
            "password": "secret123",
            "first_name": "Jane",
            "last_name": "Doe",
        }
        dumped = RegisterSchema().dump(data)
        assert "password" not in dumped


class TestLoginSchema:
    def test_loads_valid_data(self):
        data = {"email": "user@example.com", "password": "secret123"}
        result = LoginSchema().load(data)
        assert result["email"] == "user@example.com"
        assert result["password"] == "secret123"

    @pytest.mark.parametrize("missing_field", ["email", "password"])
    def test_rejects_missing_field(self, missing_field):
        data = {"email": "user@example.com", "password": "secret123"}
        del data[missing_field]
        with pytest.raises(ValidationError) as exc_info:
            LoginSchema().load(data)
        assert missing_field in exc_info.value.messages


class TestTokenSchema:
    def test_dumps_token_data(self):
        data = {"access_token": "abc.def.ghi", "refresh_token": "jkl.mno.pqr"}
        result = TokenSchema().dump(data)
        assert result["access_token"] == "abc.def.ghi"
        assert result["refresh_token"] == "jkl.mno.pqr"


class TestUserSchema:
    def test_dumps_user_data(self):
        now = datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        data = {
            "id": "abc-123",
            "email": "user@example.com",
            "first_name": "Jane",
            "last_name": "Doe",
            "created_at": now,
        }
        result = UserSchema().dump(data)
        assert result["id"] == "abc-123"
        assert result["email"] == "user@example.com"
        assert result["first_name"] == "Jane"
        assert result["last_name"] == "Doe"
        assert "created_at" in result


# ---------------------------------------------------------------------------
# Order Schemas
# ---------------------------------------------------------------------------


class TestOrderCreateSchema:
    def test_loads_all_fields(self):
        data = {
            "patient_first_name": "John",
            "patient_last_name": "Smith",
            "patient_dob": "2000-01-15",
            "insurance_provider": "Aetna",
            "insurance_id": "INS-001",
            "group_number": "GRP-100",
            "ordering_provider_name": "Dr. Brown",
            "provider_npi": "1234567890",
            "provider_phone": "555-0100",
            "equipment_type": "wheelchair",
            "equipment_description": "Standard wheelchair",
            "hcpcs_code": "K0001",
            "authorization_number": "AUTH-001",
            "authorization_status": "approved",
            "delivery_address": "123 Main St",
            "delivery_date": "2025-06-01",
            "delivery_notes": "Leave at front door",
        }
        result = OrderCreateSchema().load(data)
        assert result["patient_first_name"] == "John"
        assert result["patient_dob"] == date(2000, 1, 15)
        assert result["delivery_date"] == date(2025, 6, 1)

    def test_loads_with_no_fields(self):
        result = OrderCreateSchema().load({})
        assert result == {}

    def test_loads_partial_fields(self):
        data = {"patient_first_name": "John", "equipment_type": "wheelchair"}
        result = OrderCreateSchema().load(data)
        assert result["patient_first_name"] == "John"
        assert result["equipment_type"] == "wheelchair"
        assert "patient_last_name" not in result

    def test_date_fields(self):
        data = {"patient_dob": "1990-05-20", "delivery_date": "2025-12-31"}
        result = OrderCreateSchema().load(data)
        assert result["patient_dob"] == date(1990, 5, 20)
        assert result["delivery_date"] == date(2025, 12, 31)


class TestOrderUpdateSchema:
    def test_loads_partial_data(self):
        data = {"patient_first_name": "Updated", "insurance_provider": "New Ins"}
        result = OrderUpdateSchema().load(data)
        assert result["patient_first_name"] == "Updated"
        assert result["insurance_provider"] == "New Ins"


class TestOrderResponseSchema:
    def test_dumps_complete_order_with_document(self):
        now = datetime(2025, 3, 1, 10, 0, 0, tzinfo=timezone.utc)
        data = {
            "id": "order-1",
            "created_by": "user-1",
            "status": "pending",
            "error_message": None,
            "patient_first_name": "John",
            "patient_last_name": "Smith",
            "patient_dob": date(2000, 1, 15),
            "insurance_provider": "Aetna",
            "insurance_id": "INS-001",
            "group_number": "GRP-100",
            "ordering_provider_name": "Dr. Brown",
            "provider_npi": "1234567890",
            "provider_phone": "555-0100",
            "equipment_type": "wheelchair",
            "equipment_description": "Standard wheelchair",
            "hcpcs_code": "K0001",
            "authorization_number": "AUTH-001",
            "authorization_status": "approved",
            "delivery_address": "123 Main St",
            "delivery_date": date(2025, 6, 1),
            "delivery_notes": "Leave at front door",
            "created_at": now,
            "updated_at": now,
            "document": {
                "id": "doc-1",
                "original_filename": "order.pdf",
                "content_type": "application/pdf",
                "file_size_bytes": 12345,
                "extracted_data": {"key": "value"},
                "uploaded_at": now,
            },
        }
        result = OrderResponseSchema().dump(data)
        assert result["id"] == "order-1"
        assert result["status"] == "pending"
        assert result["patient_first_name"] == "John"
        assert result["document"]["id"] == "doc-1"
        assert result["document"]["original_filename"] == "order.pdf"

    def test_dumps_order_with_null_document(self):
        now = datetime(2025, 3, 1, 10, 0, 0, tzinfo=timezone.utc)
        data = {
            "id": "order-2",
            "created_by": "user-1",
            "status": "pending",
            "error_message": None,
            "patient_first_name": "Jane",
            "patient_last_name": "Doe",
            "created_at": now,
            "updated_at": now,
            "document": None,
        }
        result = OrderResponseSchema().dump(data)
        assert result["id"] == "order-2"
        assert result["document"] is None


class TestOrderQuerySchema:
    def test_loads_with_defaults(self):
        result = OrderQuerySchema().load({})
        assert result["page"] == 1
        assert result["per_page"] == 20
        assert result["sort_by"] == "created_at"
        assert result["sort_order"] == "desc"

    def test_validates_per_page_max(self):
        with pytest.raises(ValidationError) as exc_info:
            OrderQuerySchema().load({"per_page": 101})
        assert "per_page" in exc_info.value.messages


# ---------------------------------------------------------------------------
# Document Schema
# ---------------------------------------------------------------------------


class TestDocumentSchema:
    def test_dumps_document_data(self):
        now = datetime(2025, 2, 10, 8, 30, 0, tzinfo=timezone.utc)
        data = {
            "id": "doc-1",
            "original_filename": "report.pdf",
            "content_type": "application/pdf",
            "file_size_bytes": 54321,
            "extracted_data": {"patient": "John"},
            "uploaded_at": now,
        }
        result = DocumentSchema().dump(data)
        assert result["id"] == "doc-1"
        assert result["original_filename"] == "report.pdf"
        assert result["content_type"] == "application/pdf"
        assert result["file_size_bytes"] == 54321
        assert result["extracted_data"] == {"patient": "John"}
        assert "uploaded_at" in result


# ---------------------------------------------------------------------------
# Activity Log Schemas
# ---------------------------------------------------------------------------


class TestActivityLogSchema:
    def test_dumps_log_data(self):
        now = datetime(2025, 4, 1, 14, 0, 0, tzinfo=timezone.utc)
        data = {
            "id": "log-1",
            "user_id": "user-1",
            "endpoint": "/api/orders",
            "http_method": "GET",
            "status_code": 200,
            "ip_address": "127.0.0.1",
            "timestamp": now,
        }
        result = ActivityLogSchema().dump(data)
        assert result["id"] == "log-1"
        assert result["user_id"] == "user-1"
        assert result["endpoint"] == "/api/orders"
        assert result["http_method"] == "GET"
        assert result["status_code"] == 200
        assert result["ip_address"] == "127.0.0.1"
        assert "timestamp" in result


class TestActivityLogQuerySchema:
    def test_loads_with_defaults(self):
        result = ActivityLogQuerySchema().load({})
        assert result["page"] == 1
        assert result["per_page"] == 20

    def test_loads_with_all_filters(self):
        data = {
            "page": 2,
            "per_page": 50,
            "user_id": "user-1",
            "endpoint": "/api/orders",
            "method": "POST",
            "status_code": 201,
            "date_from": "2025-01-01T00:00:00",
            "date_to": "2025-12-31T23:59:59",
        }
        result = ActivityLogQuerySchema().load(data)
        assert result["page"] == 2
        assert result["per_page"] == 50
        assert result["user_id"] == "user-1"
        assert result["endpoint"] == "/api/orders"
        assert result["method"] == "POST"
        assert result["status_code"] == 201


# ---------------------------------------------------------------------------
# Error Schema
# ---------------------------------------------------------------------------


class TestErrorSchema:
    def test_dumps_error_envelope(self):
        data = {
            "code": "VALIDATION_ERROR",
            "message": "Invalid input",
            "details": [{"field": "email", "error": "Not a valid email"}],
        }
        result = ErrorSchema().dump(data)
        assert result["code"] == "VALIDATION_ERROR"
        assert result["message"] == "Invalid input"
        assert len(result["details"]) == 1
        assert result["details"][0]["field"] == "email"
