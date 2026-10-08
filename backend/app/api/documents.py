from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.schemas.document import DocumentUploadResponse
from app.security.policy import SecurityPolicy
from app.services.document_service import process_document
from app.services.file_validator import validate_pdf
from app.services.temporal_service import start_document_workflow


router = APIRouter(
    prefix="/documents",
    tags=["Documents"],
)


@router.post("", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    # 1. Security policy check
    policy_decision = SecurityPolicy.check_document_processing()

    if not policy_decision.allowed:
        raise HTTPException(
            status_code=403,
            detail=policy_decision.reason,
        )

    try:
        # 2. Read uploaded file
        file_bytes = await file.read()

        # 3. Validate PDF
        validate_pdf(
            filename=file.filename,
            file_bytes=file_bytes,
        )

        # 4. Save document and create database records
        result = process_document(
            db=db,
            file_bytes=file_bytes,
            filename=file.filename,
        )

        # 5. Start Temporal workflow
        workflow_result = await start_document_workflow(
            document_id=result["document_id"],
            version_id=result["version_id"],
        )

        # 6. Add workflow information to response
        result["workflow_id"] = workflow_result["workflow_id"]
        result["workflow_run_id"] = workflow_result["run_id"]

        # 7. Return response
        return result

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )