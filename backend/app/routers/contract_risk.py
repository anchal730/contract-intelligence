from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.contract_risk import ContractRisk
from app.services.contract_risk_service import ContractRiskService


router = APIRouter(
    prefix="/analysis",
    tags=["Contract Risk Analysis"],
)


@router.post("/risks")
def analyze_contract_risks(
    document_version_id: str,
    db: Session = Depends(get_db),
):
    service = ContractRiskService()

    try:
        risks = service.analyze(
            db=db,
            document_version_id=document_version_id,
        )

        return {
            "document_version_id": document_version_id,
            "risk_count": len(risks),
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

    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )


@router.get("/risks/{document_version_id}")
def get_contract_risks(
    document_version_id: str,
    db: Session = Depends(get_db),
):
    risks = (
        db.query(ContractRisk)
        .filter(
            ContractRisk.document_version_id
            == document_version_id
        )
        .order_by(ContractRisk.created_at)
        .all()
    )

    return {
        "document_version_id": document_version_id,
        "risk_count": len(risks),
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