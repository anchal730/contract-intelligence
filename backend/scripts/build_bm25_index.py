from sqlalchemy import select

from app.database import SessionLocal
from app.models.document import (
    DocumentChunk,
    DocumentVersion,
)
from app.services.bm25_service import BM25Service


def main():

    db = SessionLocal()

    try:

        statement = (
            select(DocumentVersion)
            .where(
                DocumentVersion.processing_status
                == "COMPLETED"
            )
            .order_by(
                DocumentVersion.created_at.desc()
            )
        )

        document_version = (
            db.scalars(statement)
            .first()
        )

        if not document_version:

            raise ValueError(
                "No completed document version found"
            )

        chunks = (
            db.query(DocumentChunk)
            .filter(
                DocumentChunk.document_version_id
                == document_version.id
            )
            .order_by(
                DocumentChunk.chunk_index
            )
            .all()
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
            document_version_id=document_version.id,
        )

        print(
            "\nBM25 INDEX CREATED SUCCESSFULLY"
        )

        for key, value in result.items():

            print(
                f"{key}: {value}"
            )

    finally:

        db.close()


if __name__ == "__main__":
    main()