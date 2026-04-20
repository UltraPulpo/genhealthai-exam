"""Extraction service and upload route tests."""

import io
import json
from unittest.mock import MagicMock, patch

import pytest

from app.repositories import DocumentRepository, OrderRepository
from app.services import ExtractionService
from app.utils.errors import ExtractionError
from tests.factories import OrderFactory, UserFactory

# Minimal valid PDF bytes for upload tests
_MINIMAL_PDF = (
    b"%PDF-1.0\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
    b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
    b"3 0 obj<</Type/Page/MediaBox[0 0 3 3]/Parent 2 0 R>>endobj\n"
    b"xref\n0 4\n"
    b"0000000000 65535 f \n"
    b"0000000009 00000 n \n"
    b"0000000058 00000 n \n"
    b"0000000115 00000 n \n"
    b"trailer<</Size 4/Root 1 0 R>>\nstartxref\n190\n%%EOF"
)

_LLM_RESPONSE = {
    "patient_first_name": "John",
    "patient_last_name": "Doe",
    "patient_dob": "1990-01-15",
    "insurance_provider": "Medicare",
    "insurance_id": "INS123",
    "group_number": "GRP456",
    "ordering_provider_name": "Dr. Smith",
    "provider_npi": "1234567890",
    "provider_phone": "555-0100",
    "equipment_type": "Wheelchair",
    "equipment_description": "Standard wheelchair",
    "hcpcs_code": "K0001",
    "authorization_number": "AUTH001",
    "authorization_status": "approved",
    "delivery_address": "123 Main St",
    "delivery_date": "2025-06-01",
    "delivery_notes": "Leave at door",
}


def _mock_anthropic_response(data_dict):
    """Build a mock Anthropic API response."""
    mock_resp = MagicMock()
    mock_resp.content = [MagicMock(text=json.dumps(data_dict))]
    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_resp
    return mock_client


def _extraction_service(session):
    return ExtractionService(
        order_repo=OrderRepository(session),
        doc_repo=DocumentRepository(session),
    )


# ── Service-level tests ────────────────────────────────────────────


class TestExtractionServiceUpload:
    @patch("app.services.extraction_service.anthropic.Anthropic")
    @patch("app.utils.pdf_parser.extract_text", return_value="Some medical text")
    def test_upload_and_extract_success(
        self, mock_extract, mock_anthropic_cls, db_session, app
    ):
        mock_anthropic_cls.return_value = _mock_anthropic_response(_LLM_RESPONSE)
        user = UserFactory.create(db_session)
        order = OrderFactory.create(db_session, created_by=user.id)
        svc = _extraction_service(db_session)

        file = MagicMock()
        file.filename = "order.pdf"
        file.content_type = "application/pdf"
        file.save = MagicMock()
        with patch("os.path.getsize", return_value=1024):
            result = svc.upload_and_extract(order.id, file)

        assert result.status == "completed"
        assert result.patient_first_name == "John"

    @patch("app.services.extraction_service.anthropic.Anthropic")
    @patch("app.utils.pdf_parser.extract_page_images", return_value=[])
    @patch("app.utils.pdf_parser.extract_text", return_value="")
    def test_extract_no_text(
        self, mock_extract, mock_extract_images, mock_anthropic_cls, db_session, app
    ):
        user = UserFactory.create(db_session)
        order = OrderFactory.create(db_session, created_by=user.id)
        svc = _extraction_service(db_session)

        file = MagicMock()
        file.filename = "empty.pdf"
        file.save = MagicMock()
        with patch("os.path.getsize", return_value=100):
            with pytest.raises(ExtractionError, match="no extractable text or images"):
                svc.upload_and_extract(order.id, file)

    @patch("app.services.extraction_service.anthropic.Anthropic")
    @patch(
        "app.utils.pdf_parser.extract_page_images",
        return_value=["base64imagedata=="],
    )
    @patch("app.utils.pdf_parser.extract_text", return_value="")
    def test_extract_vision_path_success(
        self, mock_extract, mock_extract_images, mock_anthropic_cls, db_session, app
    ):
        """Vision extraction path is used when text is empty but images are available."""
        mock_anthropic_cls.return_value = _mock_anthropic_response(_LLM_RESPONSE)
        user = UserFactory.create(db_session)
        order = OrderFactory.create(db_session, created_by=user.id)
        svc = _extraction_service(db_session)

        file = MagicMock()
        file.filename = "scanned.pdf"
        file.save = MagicMock()
        with patch("os.path.getsize", return_value=1024):
            result = svc.upload_and_extract(order.id, file)

        assert result.status == "completed"
        assert result.patient_first_name == "John"

    @patch("app.services.extraction_service.anthropic.Anthropic")
    @patch("app.utils.pdf_parser.extract_text", return_value="Some text")
    def test_extract_llm_timeout(
        self, mock_extract, mock_anthropic_cls, db_session, app
    ):
        import anthropic as anthropic_mod

        mock_client = MagicMock()
        mock_client.messages.create.side_effect = anthropic_mod.APITimeoutError(
            request=MagicMock()
        )
        mock_anthropic_cls.return_value = mock_client

        user = UserFactory.create(db_session)
        order = OrderFactory.create(db_session, created_by=user.id)
        svc = _extraction_service(db_session)

        file = MagicMock()
        file.filename = "timeout.pdf"
        file.save = MagicMock()
        with patch("os.path.getsize", return_value=100):
            with patch("time.sleep"):
                with pytest.raises(ExtractionError, match="unavailable"):
                    svc.upload_and_extract(order.id, file)

    @patch("app.services.extraction_service.anthropic.Anthropic")
    @patch("app.utils.pdf_parser.extract_text", return_value="Some text")
    def test_extract_llm_invalid_json(
        self, mock_extract, mock_anthropic_cls, db_session, app
    ):
        mock_resp = MagicMock()
        mock_resp.content = [MagicMock(text="not valid json {{{")]
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_resp
        mock_anthropic_cls.return_value = mock_client

        user = UserFactory.create(db_session)
        order = OrderFactory.create(db_session, created_by=user.id)
        svc = _extraction_service(db_session)

        file = MagicMock()
        file.filename = "bad_json.pdf"
        file.save = MagicMock()
        with patch("os.path.getsize", return_value=100):
            with pytest.raises(ExtractionError, match="invalid data"):
                svc.upload_and_extract(order.id, file)

    @patch("app.services.extraction_service.anthropic.Anthropic")
    @patch("app.utils.pdf_parser.extract_text", return_value="Some text")
    def test_extract_llm_empty_content(
        self, mock_extract, mock_anthropic_cls, db_session, app
    ):
        """Empty response.content array should raise ExtractionError."""
        mock_resp = MagicMock()
        mock_resp.content = []
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_resp
        mock_anthropic_cls.return_value = mock_client

        user = UserFactory.create(db_session)
        order = OrderFactory.create(db_session, created_by=user.id)
        svc = _extraction_service(db_session)

        file = MagicMock()
        file.filename = "empty_content.pdf"
        file.save = MagicMock()
        with patch("os.path.getsize", return_value=100):
            with pytest.raises(ExtractionError, match="invalid data"):
                svc.upload_and_extract(order.id, file)

    @patch("app.services.extraction_service.anthropic.Anthropic")
    @patch("app.utils.pdf_parser.extract_text", return_value="Some text")
    def test_extract_llm_non_text_block(
        self, mock_extract, mock_anthropic_cls, db_session, app
    ):
        """Non-text first block in response.content should raise ExtractionError."""
        non_text_block = MagicMock(spec=[])  # no 'text' attribute
        mock_resp = MagicMock()
        mock_resp.content = [non_text_block]
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_resp
        mock_anthropic_cls.return_value = mock_client

        user = UserFactory.create(db_session)
        order = OrderFactory.create(db_session, created_by=user.id)
        svc = _extraction_service(db_session)

        file = MagicMock()
        file.filename = "non_text_block.pdf"
        file.save = MagicMock()
        with patch("os.path.getsize", return_value=100):
            with pytest.raises(ExtractionError, match="invalid data"):
                svc.upload_and_extract(order.id, file)

    @patch("app.services.extraction_service.anthropic.Anthropic")
    @patch("app.utils.pdf_parser.extract_text", return_value="Some text")
    def test_extract_preserves_manual_fields(
        self, mock_extract, mock_anthropic_cls, db_session, app
    ):
        """LLM extraction should NOT overwrite manually set fields."""
        mock_anthropic_cls.return_value = _mock_anthropic_response(_LLM_RESPONSE)
        user = UserFactory.create(db_session)
        order = OrderFactory.create(
            db_session,
            created_by=user.id,
            patient_first_name="Manual",
        )
        svc = _extraction_service(db_session)

        file = MagicMock()
        file.filename = "preserve.pdf"
        file.save = MagicMock()
        with patch("os.path.getsize", return_value=1024):
            result = svc.upload_and_extract(order.id, file)

        # Manual value should be preserved
        assert result.patient_first_name == "Manual"

    @patch("app.services.extraction_service.anthropic.Anthropic")
    @patch("app.utils.pdf_parser.extract_text", return_value="Some text")
    def test_extract_retries_on_429(
        self, mock_extract, mock_anthropic_cls, db_session, app
    ):
        import anthropic as anthropic_mod

        mock_resp = MagicMock()
        mock_resp.content = [MagicMock(text=json.dumps(_LLM_RESPONSE))]
        mock_client = MagicMock()
        mock_client.messages.create.side_effect = [
            anthropic_mod.RateLimitError(
                message="rate limited",
                response=MagicMock(status_code=429, headers={}),
                body=None,
            ),
            mock_resp,
        ]
        mock_anthropic_cls.return_value = mock_client

        user = UserFactory.create(db_session)
        order = OrderFactory.create(db_session, created_by=user.id)
        svc = _extraction_service(db_session)

        file = MagicMock()
        file.filename = "retry.pdf"
        file.save = MagicMock()
        with patch("os.path.getsize", return_value=1024):
            with patch("time.sleep"):
                result = svc.upload_and_extract(order.id, file)

        assert result.status == "completed"
        assert mock_client.messages.create.call_count == 2


# ── Integration (API) tests ────────────────────────────────────────


class TestUploadAPI:
    @patch("app.services.extraction_service.anthropic.Anthropic")
    @patch("app.utils.pdf_parser.extract_text", return_value="Medical text here")
    def test_upload_and_extract_success_api(
        self, mock_extract, mock_anthropic_cls, client, auth_headers, db_session
    ):
        mock_anthropic_cls.return_value = _mock_anthropic_response(_LLM_RESPONSE)
        user = UserFactory.create(db_session, email="upload_api@test.com")
        order = OrderFactory.create(db_session, created_by=user.id)

        data = {"file": (io.BytesIO(_MINIMAL_PDF), "order.pdf", "application/pdf")}
        resp = client.post(
            f"/api/v1/orders/{order.id}/upload",
            data=data,
            content_type="multipart/form-data",
            headers=auth_headers,
        )
        assert resp.status_code == 200

    def test_upload_invalid_file_type(self, client, auth_headers, db_session):
        user = UserFactory.create(db_session, email="badtype@test.com")
        order = OrderFactory.create(db_session, created_by=user.id)
        data = {
            "file": (io.BytesIO(b"not a pdf"), "file.txt", "text/plain")
        }
        resp = client.post(
            f"/api/v1/orders/{order.id}/upload",
            data=data,
            content_type="multipart/form-data",
            headers=auth_headers,
        )
        assert resp.status_code == 422

    def test_upload_file_too_large(self, client, auth_headers, db_session):
        user = UserFactory.create(db_session, email="bigfile@test.com")
        order = OrderFactory.create(db_session, created_by=user.id)
        # 11 MB file
        big_data = b"\x00" * (11 * 1024 * 1024)
        data = {
            "file": (io.BytesIO(big_data), "large.pdf", "application/pdf")
        }
        resp = client.post(
            f"/api/v1/orders/{order.id}/upload",
            data=data,
            content_type="multipart/form-data",
            headers=auth_headers,
        )
        # Could be 413 (MAX_CONTENT_LENGTH) or 422 (route-level check)
        assert resp.status_code in (413, 422)

    @patch("app.services.extraction_service.anthropic.Anthropic")
    @patch("app.utils.pdf_parser.extract_text", return_value="Some text")
    def test_upload_extraction_failure(
        self, mock_extract, mock_anthropic_cls, client, auth_headers, db_session
    ):
        mock_resp = MagicMock()
        mock_resp.content = [MagicMock(text="not json")]
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_resp
        mock_anthropic_cls.return_value = mock_client

        user = UserFactory.create(db_session, email="fail_ext@test.com")
        order = OrderFactory.create(db_session, created_by=user.id)
        data = {"file": (io.BytesIO(_MINIMAL_PDF), "doc.pdf", "application/pdf")}
        resp = client.post(
            f"/api/v1/orders/{order.id}/upload",
            data=data,
            content_type="multipart/form-data",
            headers=auth_headers,
        )
        assert resp.status_code == 422

    @patch("app.services.extraction_service.anthropic.Anthropic")
    @patch("app.utils.pdf_parser.extract_page_images", return_value=[])
    @patch("app.utils.pdf_parser.extract_text", return_value="   ")
    def test_upload_no_extractable_text(
        self, mock_extract, mock_extract_images, mock_anthropic_cls, client, auth_headers, db_session
    ):
        user = UserFactory.create(db_session, email="notext@test.com")
        order = OrderFactory.create(db_session, created_by=user.id)
        data = {"file": (io.BytesIO(_MINIMAL_PDF), "empty.pdf", "application/pdf")}
        resp = client.post(
            f"/api/v1/orders/{order.id}/upload",
            data=data,
            content_type="multipart/form-data",
            headers=auth_headers,
        )
        assert resp.status_code == 422
