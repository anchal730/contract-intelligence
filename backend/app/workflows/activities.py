from pathlib import Path

import pymupdf
from temporalio import activity

from app.database import SessionLocal
from app.models.document import (
    DocumentChunk,
    DocumentVersion,
    Page,
)
from app.services.faiss_service import FAISSService

from app.services.bm25_service import BM25Service
from app.security.policy import SecurityPolicy
from app.services.chunking_service import chunk_document_pages
from app.services.document_diagnostics import diagnose_pdf
from app.services.ocr_service import extract_text_with_ocr


STORAGE_DIR = Path("storage/documents")


@activity.defn
def process_document(
    document_id: str,
    version_id: str,
) -> str:

    activity.logger.info(
        "Starting document processing",
        extra={
            "document_id": document_id,
            "version_id": version_id,
        },
    )

    # 1. Security policy check
    policy_decision = SecurityPolicy.check_document_processing()

    if not policy_decision.allowed:
        raise PermissionError(policy_decision.reason)

    # 2. Locate PDF
    document_path = STORAGE_DIR / f"{version_id}.pdf"

    if not document_path.exists():
        raise FileNotFoundError(
            f"Document file not found: {document_path}"
        )

    db = SessionLocal()
    pdf = None

    try:

        # 3. Find document version
        document_version = (
            db.query(DocumentVersion)
            .filter(
                DocumentVersion.id == version_id
            )
            .first()
        )

        if document_version is None:
            raise ValueError(
                f"Document version not found: {version_id}"
            )

        # 4. Mark document as PROCESSING
        document_version.processing_status = "PROCESSING"
        document_version.processing_error = None

        db.commit()

        activity.logger.info(
            "Document status updated to PROCESSING",
            extra={
                "document_id": document_id,
                "version_id": version_id,
            },
        )

        # 5. Diagnose PDF
        diagnostics = diagnose_pdf(
            str(document_path)
        )

        activity.logger.info(
            "PDF diagnostic completed",
            extra={
                "document_id": document_id,
                "version_id": version_id,
                "document_type": diagnostics["document_type"],
                "ocr_required": diagnostics["ocr_required"],
                "total_pages": diagnostics["total_pages"],
                "pages_with_text": diagnostics["pages_with_text"],
                "pages_without_text": diagnostics["pages_without_text"],
                "total_text_length": diagnostics["total_text_length"],
            },
        )

        # 6. Open PDF
        pdf = pymupdf.open(str(document_path))

        page_count = pdf.page_count

        # 7. Extract and persist page text
        for page_number, page in enumerate(
            pdf,
            start=1,
        ):

            # Check whether page already exists
            existing_page = (
                db.query(Page)
                .filter(
                    Page.document_version_id == version_id,
                    Page.page_number == page_number,
                )
                .first()
            )

            if existing_page:

                activity.logger.info(
                    "Page already exists, skipping",
                    extra={
                        "version_id": version_id,
                        "page_number": page_number,
                    },
                )

                continue

            # 8. Extract digital text
            text = page.get_text().strip()

            # 9. Run OCR when digital text is unavailable
            if not text:

                activity.logger.info(
                    "No digital text found. Running OCR",
                    extra={
                        "document_id": document_id,
                        "version_id": version_id,
                        "page_number": page_number,
                    },
                )

                text = extract_text_with_ocr(page)

                activity.logger.info(
                    "OCR completed",
                    extra={
                        "document_id": document_id,
                        "version_id": version_id,
                        "page_number": page_number,
                        "text_length": len(text),
                    },
                )

            # 10. Save page text
            page_record = Page(
                document_version_id=version_id,
                page_number=page_number,
                text=text,
            )

            db.add(page_record)

            activity.logger.info(
                "Extracted and saved page",
                extra={
                    "document_id": document_id,
                    "version_id": version_id,
                    "page_number": page_number,
                    "text_length": len(text),
                },
            )

        # Save newly created page records
        db.flush()

        activity.logger.info(
            "Page extraction completed",
            extra={
                "document_id": document_id,
                "version_id": version_id,
                "page_count": page_count,
            },
        )

        # 11. Fetch all pages for chunking
        page_records = (
            db.query(Page)
            .filter(
                Page.document_version_id == version_id
            )
            .order_by(Page.page_number)
            .all()
        )

        # Prepare pages for chunking
        pages_for_chunking = [
            (
                page.page_number,
                page.text,
            )
            for page in page_records
            if page.text and page.text.strip()
        ]

        activity.logger.info(
            "Preparing document chunks",
            extra={
                "document_id": document_id,
                "version_id": version_id,
                "pages_available_for_chunking": len(
                    pages_for_chunking
                ),
            },
        )

        # 12. Generate chunks
        chunks = chunk_document_pages(
            pages=pages_for_chunking,
            chunk_size=1000,
            chunk_overlap=200,
        )

        activity.logger.info(
            "Document chunks generated",
            extra={
                "document_id": document_id,
                "version_id": version_id,
                "chunk_count": len(chunks),
            },
        )

        # 13. Remove existing chunks
        # Prevent duplicate chunks during reprocessing
        db.query(DocumentChunk).filter(
            DocumentChunk.document_version_id == version_id
        ).delete(
            synchronize_session=False
        )

        # 14. Save generated chunks
        for chunk_index, chunk_data in enumerate(chunks):

            document_chunk = DocumentChunk(
                document_version_id=version_id,
                chunk_index=chunk_index,
                text=chunk_data["text"],
                start_page=chunk_data["start_page"],
                end_page=chunk_data["end_page"],
            )

            db.add(document_chunk)

        # Save chunks
        db.flush()

        activity.logger.info(
            "Document chunks saved",
            extra={
                "document_id": document_id,
                "version_id": version_id,
                "chunk_count": len(chunks),
            },
        )

        # 15. Mark document as COMPLETED
        document_version.processing_status = "COMPLETED"
        document_version.processing_error = None

        db.commit()

        activity.logger.info(
            "Document processing completed",
            extra={
                "document_id": document_id,
                "version_id": version_id,
                "page_count": page_count,
                "chunk_count": len(chunks),
                "document_type": diagnostics["document_type"],
                "ocr_required": diagnostics["ocr_required"],
            },
        )

        return (
            f"Processed document {document_id}, "
            f"version {version_id}, "
            f"pages {page_count}, "
            f"chunks {len(chunks)}, "
            f"type {diagnostics['document_type']}, "
            f"OCR required {diagnostics['ocr_required']}"
        )

    except Exception as exc:

        # 16. Roll back uncommitted changes
        db.rollback()

        activity.logger.exception(
            "Document processing failed",
            extra={
                "document_id": document_id,
                "version_id": version_id,
            },
        )

        # 17. Mark document as FAILED
        try:

            failed_version = (
                db.query(DocumentVersion)
                .filter(
                    DocumentVersion.id == version_id
                )
                .first()
            )

            if failed_version is not None:

                failed_version.processing_status = "FAILED"

                failed_version.processing_error = str(
                    exc
                )[:5000]

                db.commit()

                activity.logger.info(
                    "Document status updated to FAILED",
                    extra={
                        "document_id": document_id,
                        "version_id": version_id,
                    },
                )

        except Exception:

            db.rollback()

            activity.logger.exception(
                "Failed to update document status to FAILED",
                extra={
                    "document_id": document_id,
                    "version_id": version_id,
                },
            )

        # 18. Re-raise exception for Temporal
        raise

    finally:

        # 19. Close PDF
        if pdf is not None:
            pdf.close()

        # 20. Close database session
        db.close()
        
@activity.defn(name="build_faiss_index")
def build_faiss_index(document_version_id: str) -> dict:
    """
    Build a FAISS index for a processed document version.
    """
    db = SessionLocal()

    try:
        service = FAISSService()

        result = service.build_index(
            db=db,
            document_version_id=document_version_id,
        )

        return result

    except Exception as exc:
        activity.logger.error(
            f"FAISS index creation failed: {exc}"
        )
        raise

    finally:
        db.close()    
        
@activity.defn(name="build_bm25_index")
def build_bm25_index(document_version_id: str) -> dict:
    """
    Build a BM25 index for a processed document version.
    """

    db = SessionLocal()

    try:
        chunks = (
            db.query(DocumentChunk)
            .filter(
                DocumentChunk.document_version_id
                == document_version_id
            )
            .order_by(DocumentChunk.chunk_index)
            .all()
        )

        if not chunks:
            raise ValueError(
                f"No document chunks found for version "
                f"{document_version_id}"
            )

        chunk_data = [
            {
                "chunk_index": chunk.chunk_index,
                "text": chunk.text,
                "start_page": chunk.start_page,
                "end_page": chunk.end_page,
            }
            for chunk in chunks
        ]

        service = BM25Service()

        result = service.build_index(
            chunks=chunk_data,
            document_version_id=document_version_id,
        )

        activity.logger.info(
            f"BM25 index created successfully: {result}"
        )

        return result

    except Exception as exc:
        activity.logger.error(
            f"BM25 index creation failed: {exc}"
        )
        raise

    finally:
        db.close()        
