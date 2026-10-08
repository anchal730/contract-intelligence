from typing import Any

from sqlalchemy.orm import Session

from app.models.contract_extraction import ContractExtractionRecord
from app.models.contract_risk import ContractRisk


class ContractRiskService:

    def analyze(
        self,
        db: Session,
        document_version_id: str,
    ) -> list[ContractRisk]:

        extraction_record = (
            db.query(ContractExtractionRecord)
            .filter(
                ContractExtractionRecord.document_version_id
                == document_version_id
            )
            .first()
        )

        if extraction_record is None:
            raise ValueError(
                "No contract extraction found for "
                f"document version: {document_version_id}"
            )

        extraction = extraction_record.extraction_data

        # Remove previously generated risks so the operation is idempotent.
        db.query(ContractRisk).filter(
            ContractRisk.document_version_id
            == document_version_id
        ).delete(
            synchronize_session=False
        )

        risks: list[dict[str, Any]] = []

        self._check_penalties(
            extraction,
            risks,
        )

        self._check_missing_dates(
            extraction,
            risks,
        )

        self._check_governing_law(
            extraction,
            risks,
        )

        self._check_termination(
            extraction,
            risks,
        )

        self._check_force_majeure(
            extraction,
            risks,
        )

        self._check_dispute_resolution(
            extraction,
            risks,
        )

        records: list[ContractRisk] = []

        for risk in risks:

            record = ContractRisk(
                document_version_id=document_version_id,
                risk_type=risk["risk_type"],
                severity=risk["severity"],
                title=risk["title"],
                description=risk["description"],
                evidence=risk.get("evidence"),
                source_pages=risk.get("source_pages", []),
                rule_code=risk["rule_code"],
            )

            db.add(record)
            records.append(record)

        db.commit()

        for record in records:
            db.refresh(record)

        return records

    @staticmethod
    def _check_penalties(
        extraction: dict[str, Any],
        risks: list[dict[str, Any]],
    ) -> None:

        penalties = extraction.get("penalties") or []

        for penalty in penalties:

            value = str(
                penalty.get("value") or ""
            )

            if not value:
                continue

            risks.append(
                {
                    "risk_type": "PENALTY",
                    "severity": "HIGH",
                    "title": "Contract penalty clause detected",
                    "description": (
                        "The contract contains a penalty provision. "
                        "Review the applicable trigger, calculation method "
                        "and maximum exposure."
                    ),
                    "evidence": penalty.get("evidence"),
                    "source_pages": penalty.get(
                        "source_pages",
                        [],
                    ),
                    "rule_code": "PENALTY_CLAUSE",
                }
            )

    @staticmethod
    def _check_missing_dates(
        extraction: dict[str, Any],
        risks: list[dict[str, Any]],
    ) -> None:

        effective_date = extraction.get(
            "effective_date"
        ) or {}

        expiry_date = extraction.get(
            "expiry_date"
        ) or {}

        duration = extraction.get(
            "duration"
        ) or {}

        missing_fields = []

        if not effective_date.get("value"):
            missing_fields.append("effective date")

        if not expiry_date.get("value"):
            missing_fields.append("expiry date")

        if not duration.get("value"):
            missing_fields.append("contract duration")

        if missing_fields:

            risks.append(
                {
                    "risk_type": "MISSING_INFORMATION",
                    "severity": "MEDIUM",
                    "title": "Contract timing information is incomplete",
                    "description": (
                        "The structured extraction does not contain "
                        "supported values for: "
                        + ", ".join(missing_fields)
                        + "."
                    ),
                    "evidence": None,
                    "source_pages": [],
                    "rule_code": "MISSING_CONTRACT_DATES",
                }
            )

    @staticmethod
    def _check_governing_law(
        extraction: dict[str, Any],
        risks: list[dict[str, Any]],
    ) -> None:

        governing_law = extraction.get(
            "governing_law"
        ) or {}

        if not governing_law.get("value"):

            risks.append(
                {
                    "risk_type": "MISSING_INFORMATION",
                    "severity": "MEDIUM",
                    "title": "Governing law is not identified",
                    "description": (
                        "No supported governing-law provision was "
                        "identified in the structured extraction."
                    ),
                    "evidence": None,
                    "source_pages": [],
                    "rule_code": "MISSING_GOVERNING_LAW",
                }
            )

    @staticmethod
    def _check_termination(
        extraction: dict[str, Any],
        risks: list[dict[str, Any]],
    ) -> None:

        termination_clauses = extraction.get(
            "termination_clauses"
        ) or []

        if not termination_clauses:
            return

        for clause in termination_clauses:

            value = str(
                clause.get("value") or ""
            ).lower()

            if "30" in value and "notice" in value:

                risks.append(
                    {
                        "risk_type": "TERMINATION",
                        "severity": "MEDIUM",
                        "title": "Termination on notice detected",
                        "description": (
                            "The contract contains a termination "
                            "mechanism based on a notice period. "
                            "Review the notice requirements and "
                            "termination consequences."
                        ),
                        "evidence": clause.get("evidence"),
                        "source_pages": clause.get(
                            "source_pages",
                            [],
                        ),
                        "rule_code": "NOTICE_TERMINATION",
                    }
                )

    @staticmethod
    def _check_force_majeure(
        extraction: dict[str, Any],
        risks: list[dict[str, Any]],
    ) -> None:

        force_majeure = extraction.get(
            "force_majeure"
        ) or {}

        value = str(
            force_majeure.get("value") or ""
        )

        if not value:
            return

        risks.append(
            {
                "risk_type": "FORCE_MAJEURE",
                "severity": "LOW",
                "title": "Force majeure clause detected",
                "description": (
                    "The contract contains a force-majeure provision. "
                    "Review the covered events and exclusions."
                ),
                "evidence": force_majeure.get(
                    "evidence"
                ),
                "source_pages": force_majeure.get(
                    "source_pages",
                    [],
                ),
                "rule_code": "FORCE_MAJEURE_REVIEW",
            }
        )

    @staticmethod
    def _check_dispute_resolution(
        extraction: dict[str, Any],
        risks: list[dict[str, Any]],
    ) -> None:

        dispute = extraction.get(
            "dispute_resolution"
        ) or {}

        if not dispute.get("value"):
            risks.append(
                {
                    "risk_type": "MISSING_INFORMATION",
                    "severity": "MEDIUM",
                    "title": "Dispute resolution is not identified",
                    "description": (
                        "No supported dispute-resolution provision "
                        "was identified."
                    ),
                    "evidence": None,
                    "source_pages": [],
                    "rule_code": "MISSING_DISPUTE_RESOLUTION",
                }
            )