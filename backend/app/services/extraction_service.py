"""Extraction service."""

import json
import os
import re
import time
import uuid

import anthropic
from flask import current_app

from app.repositories import DocumentRepository, OrderRepository
from app.utils.errors import ExtractionError, NotFoundError

_EXTRACTED_FIELDS = [
    "patient_first_name",
    "patient_last_name",
    "patient_dob",
    "insurance_provider",
    "insurance_id",
    "group_number",
    "ordering_provider_name",
    "provider_npi",
    "provider_phone",
    "equipment_type",
    "equipment_description",
    "hcpcs_code",
    "authorization_number",
    "authorization_status",
    "delivery_address",
    "delivery_date",
    "delivery_notes",
]

_DATE_FIELDS = {"patient_dob", "delivery_date"}

_SYSTEM_PROMPT = (
    "You are a medical document data extraction assistant. Your task is to extract structured data "
    "from Durable Medical Equipment (DME) order documents. Extract only information that is "
    "explicitly present in the document text. If a field is not found in the document text, set "
    "its value to null. Respond ONLY with a valid JSON object matching the specified schema — no "
    "markdown, no explanation, no additional text."
)

_USER_PROMPT_TEMPLATE = (
    "Extract the following fields from this DME order document and return them as a JSON object:"
    "\n\n{text}\n\n"
    "Return a JSON object with these exact keys:\n"
    "- patient_first_name (string or null)\n"
    "- patient_last_name (string or null)\n"
    "- patient_dob (string in YYYY-MM-DD format, or null)\n"
    "- insurance_provider (string or null)\n"
    "- insurance_id (string or null)\n"
    "- group_number (string or null)\n"
    "- ordering_provider_name (string or null)\n"
    "- provider_npi (string or null)\n"
    "- provider_phone (string or null)\n"
    "- equipment_type (string or null)\n"
    "- equipment_description (string or null)\n"
    "- hcpcs_code (string or null)\n"
    "- authorization_number (string or null)\n"
    "- authorization_status (string or null)\n"
    "- delivery_address (string or null)\n"
    "- delivery_date (string in YYYY-MM-DD format, or null)\n"
    "- delivery_notes (string or null)"
)


class ExtractionService:
    def __init__(self, order_repo: OrderRepository, doc_repo: DocumentRepository):
        self.order_repo = order_repo
        self.doc_repo = doc_repo

    def upload_and_extract(self, order_id: str, file):
        order = self.order_repo.get_by_id(order_id)
        if order is None:
            raise NotFoundError("Order not found")

        existing_doc = self.doc_repo.get_by_order_id(order_id)
        if existing_doc is not None:
            try:
                os.remove(existing_doc.stored_path)
            except (FileNotFoundError, OSError):
                pass
            self.doc_repo.delete(existing_doc)
            for field in _EXTRACTED_FIELDS:
                setattr(order, field, None)
            order.error_message = None

        stored_path, file_size = self._save_file(file)

        order.status = "processing"
        self.order_repo.commit()

        try:
            text = self._extract_text(stored_path)

            if not text.strip():
                order.status = "failed"
                order.error_message = "PDF contains no extractable text"
                self.order_repo.commit()
                raise ExtractionError("PDF contains no extractable text")

            data = self._call_llm(text, order)
            cleaned = self._validate_extraction(data)
            self._populate_order(order, cleaned)

            self.doc_repo.create(
                {
                    "order_id": order.id,
                    "original_filename": file.filename,
                    "stored_path": stored_path,
                    "file_size_bytes": file_size,
                    "content_type": "application/pdf",
                }
            )

            order.status = "completed"
            self.order_repo.commit()
            return order
        except ExtractionError:
            try:
                os.remove(stored_path)
            except OSError:
                pass
            raise

    def _save_file(self, file) -> tuple[str, int]:
        from flask import current_app

        upload_folder = current_app.config["UPLOAD_FOLDER"]
        os.makedirs(upload_folder, exist_ok=True)
        filename = f"{uuid.uuid4()}.pdf"
        stored_path = os.path.join(upload_folder, filename)
        file.save(stored_path)
        file_size = os.path.getsize(stored_path)
        return (stored_path, file_size)

    def _extract_text(self, file_path: str) -> str:
        from app.utils import pdf_parser

        return pdf_parser.extract_text(file_path)

    def _call_llm(self, text: str, order) -> dict:
        model = current_app.config.get("ANTHROPIC_MODEL", "claude-3-5-haiku-20241022")
        max_tokens = current_app.config.get("ANTHROPIC_MAX_TOKENS", 1024)
        timeout = current_app.config.get("ANTHROPIC_TIMEOUT", 30)
        max_retries = current_app.config.get("ANTHROPIC_MAX_RETRIES", 3)

        client = anthropic.Anthropic(timeout=timeout)
        user_prompt = _USER_PROMPT_TEMPLATE.format(text=text)

        last_exc = None
        for attempt in range(max_retries):
            try:
                response = client.messages.create(
                    model=model,
                    max_tokens=max_tokens,
                    system=_SYSTEM_PROMPT,
                    messages=[{"role": "user", "content": user_prompt}],
                )
                break
            except (anthropic.RateLimitError, anthropic.APITimeoutError) as exc:
                last_exc = exc
                time.sleep(2**attempt)
            except anthropic.APIStatusError as exc:
                if exc.status_code >= 500:
                    last_exc = exc
                    time.sleep(2**attempt)
                else:
                    raise
        else:
            order.status = "failed"
            order.error_message = "AI extraction service unavailable"
            self.order_repo.commit()
            raise ExtractionError("AI extraction service unavailable") from last_exc

        try:
            data = json.loads(response.content[0].text)
        except json.JSONDecodeError as exc:
            order.status = "failed"
            order.error_message = "AI extraction returned invalid data"
            self.order_repo.commit()
            raise ExtractionError("AI extraction returned invalid data") from exc

        if not isinstance(data, dict):
            order.status = "failed"
            order.error_message = "AI extraction returned invalid data"
            self.order_repo.commit()
            raise ExtractionError("AI extraction returned invalid data")

        return data

    def _validate_extraction(self, data: dict) -> dict:
        cleaned = {}
        for key in _EXTRACTED_FIELDS:
            value = data.get(key)
            if value is not None:
                value = str(value)
            if key in _DATE_FIELDS and value is not None:
                if not re.match(r"^\d{4}-\d{2}-\d{2}$", value):
                    value = None
                else:
                    from datetime import date

                    y, m, d = value.split("-")
                    try:
                        value = date(int(y), int(m), int(d))
                    except ValueError:
                        value = None
            cleaned[key] = value
        return cleaned

    def _populate_order(self, order, data: dict) -> None:
        for key, value in data.items():
            if value is not None:
                current = getattr(order, key, None)
                if current is None or current == "":
                    setattr(order, key, value)
