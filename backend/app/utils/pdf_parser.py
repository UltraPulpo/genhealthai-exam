"""PDF text extraction utility."""

from __future__ import annotations

import pdfplumber

from app.utils.errors import ExtractionError


def extract_text(file_path: str) -> str:
    """Extract all text from a PDF file.

    Returns the concatenated text of all pages, or an empty string if no
    text could be extracted.  Wraps pdfplumber errors in
    :class:`~app.utils.errors.ExtractionError`.
    """
    try:
        with pdfplumber.open(file_path) as pdf:
            pages: list[str] = []
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    pages.append(text)
            return "\n".join(pages) if pages else ""
    except ExtractionError:
        raise
    except Exception as exc:
        raise ExtractionError("Failed to extract text from PDF file") from exc
