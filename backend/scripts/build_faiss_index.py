from sqlalchemy import select

from app.database import SessionLocal
from app.models.document import DocumentVersion
from app.services.faiss_service import FAISSService


def main():

    db = SessionLocal()

    try:

        statement = (
            select(DocumentVersion)
            .where(
                DocumentVersion.processing_status == "COMPLETED"
            )
            .order_by(DocumentVersion.created_at.desc())
        )

        document_version = db.scalars(statement).first()

        if not document_version:
            raise ValueError(
                "No completed document version found"
            )

        print(
            f"Selected document version: "
            f"{document_version.id}"
        )

        service = FAISSService()

        result = service.build_index(
            db=db,
            document_version_id=document_version.id,
        )

        print("\nFAISS INDEX CREATED SUCCESSFULLY")

        for key, value in result.items():
            print(f"{key}: {value}")

    finally:
        db.close()


if __name__ == "__main__":
    main()