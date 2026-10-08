import pymupdf


def diagnose_pdf(file_path: str) -> dict:
    pdf = pymupdf.open(file_path)

    try:
        total_pages = pdf.page_count
        pages_with_text = 0
        pages_without_text = 0
        total_text_length = 0

        for page in pdf:
            text = page.get_text().strip()

            if text:
                pages_with_text += 1
                total_text_length += len(text)
            else:
                pages_without_text += 1

            total_text_length += 0

        if pages_with_text == 0:
            document_type = "SCANNED"
        elif pages_without_text > 0:
            document_type = "MIXED"
        else:
            document_type = "DIGITAL"

        return {
            "total_pages": total_pages,
            "pages_with_text": pages_with_text,
            "pages_without_text": pages_without_text,
            "total_text_length": total_text_length,
            "document_type": document_type,
            "ocr_required": document_type in {"SCANNED", "MIXED"},
        }

    finally:
        pdf.close()