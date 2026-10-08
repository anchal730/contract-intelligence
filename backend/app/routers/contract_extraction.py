
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.document import DocumentVersion
from app.models.contract_extraction import ContractExtractionRecord
from app.services.contract_extraction_service import (
    ContractExtractionService,
)

router = APIRouter(
    prefix="/analysis",
    tags=["Contract Analysis"],
)


class ContractExtractionRequest(BaseModel):
    document_version_id: str = Field(min_length=1)


@router.post("/extract")
def extract_contract(
    request: ContractExtractionRequest,
    db: Session = Depends(get_db),
):
    try:
        # Confirm the document version exists.
        document_version = (
            db.query(DocumentVersion)
            .filter(
                DocumentVersion.id == request.document_version_id
            )
            .first()
        )

        if document_version is None:
            raise HTTPException(
                status_code=404,
                detail="Document version not found.",
            )

        # Run the existing extraction service.
        service = ContractExtractionService()
        result = service.extract_contract(
            document_version_id=request.document_version_id
        )

        # Convert Pydantic models to JSON-compatible dictionaries.
        if hasattr(result, "model_dump"):
            extraction_data = result.model_dump(mode="json")
        elif isinstance(result, dict):
            extraction_data = result
        else:
            raise ValueError(
                "Extraction service returned an unsupported result type."
            )

        # Find the existing record so repeated requests do not
        # create duplicate extraction records.
        record = (
            db.query(ContractExtractionRecord)
            .filter(
                ContractExtractionRecord.document_version_id
                == request.document_version_id
            )
            .first()
        )

        if record is None:
            record = ContractExtractionRecord(
                document_version_id=request.document_version_id,
                extraction_data=extraction_data,
                extraction_status="EXTRACTED",
            )
            db.add(record)
        else:
            record.extraction_data = extraction_data
            record.extraction_status = "EXTRACTED"

        db.commit()
        db.refresh(record)

        return {
            "document_version_id": request.document_version_id,
            "record_id": record.id,
            "extraction_status": record.extraction_status,
            "saved": True,
            "extraction": record.extraction_data,
        }

    except HTTPException:
        db.rollback()
        raise

    except ValueError as exc:
        db.rollback()
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Contract extraction or persistence failed: {exc}",
        ) from exc


@router.get("/extractions/{document_version_id}")
def get_saved_extraction(
    document_version_id: str,
    db: Session = Depends(get_db),
):
    record = (
        db.query(ContractExtractionRecord)
        .filter(
            ContractExtractionRecord.document_version_id
            == document_version_id
        )
        .first()
    )

    if record is None:
        raise HTTPException(
            status_code=404,
            detail="No saved extraction found for this document version.",
        )

    return {
        "document_version_id": record.document_version_id,
        "record_id": record.id,
        "extraction_status": record.extraction_status,
        "created_at": record.created_at,
        "updated_at": record.updated_at,
        "extraction": record.extraction_data,
    }