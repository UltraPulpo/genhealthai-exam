"""Tests for app.utils.errors and app.utils.pdf_parser."""

import json

import pytest
from flask import Flask, request

from app.utils.errors import (
    AppError,
    AuthenticationError,
    BusinessValidationError,
    ConflictError,
    DatabaseError,
    ExtractionError,
    NotFoundError,
    RateLimitError,
    register_error_handlers,
)
from app.utils.pdf_parser import extract_text

# ---------------------------------------------------------------------------
# Error class hierarchy tests
# ---------------------------------------------------------------------------


class TestAppError:
    def test_default_attributes(self):
        err = AppError("something broke")
        assert err.message == "something broke"
        assert err.status_code == 500
        assert err.code == "APP_ERROR"
        assert err.details == []

    def test_custom_details(self):
        details = [{"field": "name", "issue": "required"}]
        err = AppError("bad", details=details)
        assert err.details == details

    def test_is_exception(self):
        assert issubclass(AppError, Exception)


class TestBusinessValidationError:
    def test_defaults(self):
        err = BusinessValidationError("invalid input")
        assert err.code == "BUSINESS_VALIDATION_ERROR"
        assert err.status_code == 422
        assert err.message == "invalid input"
        assert err.details == []

    def test_inherits_app_error(self):
        assert issubclass(BusinessValidationError, AppError)


class TestAuthenticationError:
    def test_defaults(self):
        err = AuthenticationError("bad token")
        assert err.code == "AUTHENTICATION_ERROR"
        assert err.status_code == 401
        assert err.message == "bad token"

    def test_inherits_app_error(self):
        assert issubclass(AuthenticationError, AppError)


class TestNotFoundError:
    def test_defaults(self):
        err = NotFoundError("no such item")
        assert err.code == "NOT_FOUND"
        assert err.status_code == 404
        assert err.message == "no such item"

    def test_inherits_app_error(self):
        assert issubclass(NotFoundError, AppError)


class TestConflictError:
    def test_defaults(self):
        err = ConflictError("already exists")
        assert err.code == "CONFLICT"
        assert err.status_code == 409
        assert err.message == "already exists"

    def test_inherits_app_error(self):
        assert issubclass(ConflictError, AppError)


class TestExtractionError:
    def test_defaults(self):
        err = ExtractionError("parse failed")
        assert err.code == "EXTRACTION_FAILED"
        assert err.status_code == 422
        assert err.message == "parse failed"

    def test_inherits_app_error(self):
        assert issubclass(ExtractionError, AppError)


class TestRateLimitError:
    def test_defaults(self):
        err = RateLimitError("slow down")
        assert err.code == "RATE_LIMIT_EXCEEDED"
        assert err.status_code == 429
        assert err.message == "slow down"

    def test_inherits_app_error(self):
        assert issubclass(RateLimitError, AppError)


class TestDatabaseError:
    def test_defaults(self):
        err = DatabaseError("db crashed")
        assert err.code == "INTERNAL_ERROR"
        assert err.status_code == 500
        assert err.message == "db crashed"

    def test_inherits_app_error(self):
        assert issubclass(DatabaseError, AppError)


# ---------------------------------------------------------------------------
# Error handler tests
# ---------------------------------------------------------------------------


@pytest.fixture()
def error_app():
    """Minimal Flask app with registered error handlers."""
    app = Flask(__name__)
    app.config["TESTING"] = True
    register_error_handlers(app)

    @app.route("/raise-app-error")
    def raise_app_error():
        raise AppError("generic app error")

    @app.route("/raise-not-found")
    def raise_not_found():
        raise NotFoundError("item missing")

    @app.route("/raise-validation")
    def raise_validation():
        raise BusinessValidationError("bad data", details=[{"field": "x", "issue": "required"}])

    @app.route("/raise-unexpected")
    def raise_unexpected():
        raise RuntimeError("kaboom")

    @app.route("/upload", methods=["POST"])
    def upload():
        _ = request.data
        return "ok"

    return app


class TestRegisterErrorHandlers:
    def test_app_error_handler(self, error_app):
        client = error_app.test_client()
        resp = client.get("/raise-app-error")
        assert resp.status_code == 500
        data = resp.get_json()
        assert data["error"]["code"] == "APP_ERROR"
        assert data["error"]["message"] == "generic app error"
        assert data["error"]["details"] == []

    def test_not_found_error_handler(self, error_app):
        client = error_app.test_client()
        resp = client.get("/raise-not-found")
        assert resp.status_code == 404
        data = resp.get_json()
        assert data["error"]["code"] == "NOT_FOUND"
        assert data["error"]["message"] == "item missing"

    def test_validation_error_with_details(self, error_app):
        client = error_app.test_client()
        resp = client.get("/raise-validation")
        assert resp.status_code == 422
        data = resp.get_json()
        assert data["error"]["code"] == "BUSINESS_VALIDATION_ERROR"
        assert data["error"]["details"] == [{"field": "x", "issue": "required"}]

    def test_catch_all_handler_returns_generic_message(self, error_app):
        client = error_app.test_client()
        resp = client.get("/raise-unexpected")
        assert resp.status_code == 500
        data = resp.get_json()
        assert data["error"]["code"] == "INTERNAL_ERROR"
        assert data["error"]["message"] == "An unexpected error occurred"
        assert data["error"]["details"] == []
        # Must NOT leak the raw exception message
        assert "kaboom" not in json.dumps(data)

    def test_request_entity_too_large(self, error_app):
        error_app.config["MAX_CONTENT_LENGTH"] = 10  # 10 bytes
        client = error_app.test_client()
        resp = client.post(
            "/upload",
            data=b"x" * 100,
            content_type="application/octet-stream",
        )
        assert resp.status_code == 413
        data = resp.get_json()
        assert data["error"]["code"] == "FILE_TOO_LARGE"


# ---------------------------------------------------------------------------
# PDF parser tests
# ---------------------------------------------------------------------------


def _make_pdf(text: str, path: str) -> str:
    """Create a minimal single-page PDF containing *text* using reportlab."""
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas

    c = canvas.Canvas(path, pagesize=letter)
    c.drawString(72, 720, text)
    c.save()
    return path


class TestExtractText:
    def test_valid_pdf(self, tmp_path):
        pdf_path = str(tmp_path / "sample.pdf")
        _make_pdf("Hello World", pdf_path)
        result = extract_text(pdf_path)
        assert "Hello World" in result

    def test_empty_pdf(self, tmp_path):
        """A PDF with no drawable text should return an empty string."""
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas

        pdf_path = str(tmp_path / "empty.pdf")
        c = canvas.Canvas(pdf_path, pagesize=letter)
        c.showPage()
        c.save()
        result = extract_text(pdf_path)
        assert result == ""

    def test_nonexistent_file_raises_extraction_error(self):
        with pytest.raises(ExtractionError):
            extract_text("/nonexistent/path/fake.pdf")

    def test_multi_page_pdf(self, tmp_path):
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas

        pdf_path = str(tmp_path / "multi.pdf")
        c = canvas.Canvas(pdf_path, pagesize=letter)
        c.drawString(72, 720, "Page One")
        c.showPage()
        c.drawString(72, 720, "Page Two")
        c.save()
        result = extract_text(pdf_path)
        assert "Page One" in result
        assert "Page Two" in result
