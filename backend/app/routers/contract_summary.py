from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.contract_extraction import ContractExtractionRecord
from app.models.contract_risk import ContractRisk
from app.models.document import DocumentVersion


router = APIRouter(
    prefix="/analysis",
    tags=["Contract Analysis Summary"],
)


@router.get("/summary/{document_version_id}")
def get_contract_summary(
    document_version_id: str,
    db: Session = Depends(get_db),
):
    # ---------------------------------------------------------
    # 1. Verify document version exists
    # ---------------------------------------------------------
    document_version = (
        db.query(DocumentVersion)
        .filter(
            DocumentVersion.id == document_version_id
        )
        .first()
    )

    if document_version is None:
        raise HTTPException(
            status_code=404,
            detail="Document version not found",
        )

    # ---------------------------------------------------------
    # 2. Get saved extraction
    # ---------------------------------------------------------
    extraction_record = (
        db.query(ContractExtractionRecord)
        .filter(
            ContractExtractionRecord.document_version_id
            == document_version_id
        )
        .first()
    )

    if extraction_record is None:
        raise HTTPException(
            status_code=404,
            detail="Contract extraction not found",
        )

    extraction = extraction_record.extraction_data

    # ---------------------------------------------------------
    # 3. Get saved risks
    # ---------------------------------------------------------
    risks = (
        db.query(ContractRisk)
        .filter(
            ContractRisk.document_version_id
            == document_version_id
        )
        .order_by(ContractRisk.created_at)
        .all()
    )

    # ---------------------------------------------------------
    # 4. Calculate risk summary
    # ---------------------------------------------------------
    high_count = sum(
        1 for risk in risks
        if risk.severity == "HIGH"
    )

    medium_count = sum(
        1 for risk in risks
        if risk.severity == "MEDIUM"
    )

    low_count = sum(
        1 for risk in risks
        if risk.severity == "LOW"
    )

    # ---------------------------------------------------------
    # 5. Return dashboard-friendly response
    # ---------------------------------------------------------
    return {
        "document_version_id": document_version_id,

        "document": {
            "version_number": document_version.version_number,
            "processing_status": document_version.processing_status,
            "created_at": document_version.created_at,
        },

        "contract": {
            "title": extraction.get("contract_title"),
            "parties": extraction.get("parties", []),
            "effective_date": extraction.get(
                "effective_date"
            ),
            "expiry_date": extraction.get(
                "expiry_date"
            ),
            "duration": extraction.get(
                "duration"
            ),
        },

        "commercial": {
            "scope_of_work": extraction.get(
                "scope_of_work"
            ),
            "payment_terms": extraction.get(
                "payment_terms"
            ),
            "penalties": extraction.get(
                "penalties",
                [],
            ),
        },

        "legal": {
            "termination_clauses": extraction.get(
                "termination_clauses",
                [],
            ),
            "dispute_resolution": extraction.get(
                "dispute_resolution"
            ),
            "force_majeure": extraction.get(
                "force_majeure"
            ),
            "governing_law": extraction.get(
                "governing_law"
            ),
        },

        "obligations": extraction.get(
            "obligations",
            [],
        ),

        "important_dates": extraction.get(
            "important_dates",
            [],
        ),

        "risk_summary": {
            "total": len(risks),
            "high": high_count,
            "medium": medium_count,
            "low": low_count,
        },

        "risks": [
            {
                "id": risk.id,
                "risk_type": risk.risk_type,
                "severity": risk.severity,
                "title": risk.title,
                "description": risk.description,
                "evidence": risk.evidence,
                "source_pages": risk.source_pages,
                "rule_code": risk.rule_code,
            }
            for risk in risks
        ],
    }