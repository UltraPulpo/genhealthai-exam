"""PDF text and image extraction utility."""

from __future__ import annotations

import base64
import io

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


def extract_page_images(file_path: str, resolution: int = 150) -> list[str]:
    """Convert PDF pages to base64-encoded PNG images for vision API.

    Returns a list of base64-encoded PNG strings, one per page.
    """
    try:
        images: list[str] = []
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_img = page.to_image(resolution=resolution)
                buf = io.BytesIO()
                page_img.original.save(buf, format="PNG")
                images.append(base64.b64encode(buf.getvalue()).decode())
        return images
    except Exception as exc:
        raise ExtractionError("Failed to convert PDF pages to images") from exc
