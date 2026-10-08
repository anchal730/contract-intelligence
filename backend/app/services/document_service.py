from pathlib import Path

from sqlalchemy.orm import Session

from app.models.document import Document, DocumentVersion
from app.utils.hashing import calculate_sha256


STORAGE_DIR = Path("storage/documents")
STORAGE_DIR.mkdir(parents=True, exist_ok=True)


def process_document(
    db: Session,
    file_bytes: bytes,
    filename: str,
):
    # -------------------------
    # 1. Create Document
    # -------------------------

    document = Document(
        original_filename=filename,
    )

    db.add(document)
    db.flush()

    # -------------------------
    # 2. Calculate file hash
    # -------------------------

    sha256 = calculate_sha256(file_bytes)

    # -------------------------
    # 3. Create DocumentVersion
    # -------------------------

    version = DocumentVersion(
        document_id=document.id,
        version_number=1,
        sha256=sha256,
        file_size=len(file_bytes),
        processing_status="UPLOADED",
        processing_error=None,
    )

    db.add(version)
    db.flush()

    # -------------------------
    # 4. Save original PDF
    # -------------------------

    document_path = STORAGE_DIR / f"{version.id}.pdf"

    document_path.write_bytes(file_bytes)

    # -------------------------
    # 5. Commit metadata
    # -------------------------

    db.commit()

    # -------------------------
    # 6. Return upload details
    # -------------------------

    return {
        "document_id": document.id,
        "version_id": version.id,
        "filename": filename,
        "file_size": len(file_bytes),
        "sha256": sha256,
        "status": "UPLOADED",
        "pages": [],
    }