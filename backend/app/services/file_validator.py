from pathlib import Path

import fitz

from app.config import settings


def validate_pdf(
    filename: str,
    file_bytes: bytes,
) -> None:

    # 1. Filename validation
    if not filename:
        raise ValueError("Filename is required")

    extension = Path(filename).suffix.lower()

    if extension != settings.allowed_extension:
        raise ValueError("Only PDF files are allowed")

    # 2. Size validation
    if len(file_bytes) > settings.max_file_size:
        raise ValueError(
            f"File exceeds maximum size of "
            f"{settings.max_file_size // (1024 * 1024)} MB"
        )

    # 3. Empty file validation
    if len(file_bytes) == 0:
        raise ValueError("Uploaded file is empty")

    # 4. PDF structure validation
    try:
        pdf = fitz.open(
            stream=file_bytes,
            filetype="pdf",
        )

        if pdf.page_count == 0:
            raise ValueError("PDF contains no pages")

        pdf.close()

    except Exception as exc:
        raise ValueError(
            "Uploaded file is not a valid PDF"
        ) from exc