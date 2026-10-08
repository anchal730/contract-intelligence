from pydantic import BaseModel, Field


class ExtractedValue(BaseModel):
    value: str | None = None
    evidence: str | None = None
    source_pages: list[int] = Field(default_factory=list)


class ContractExtraction(BaseModel):
    contract_title: ExtractedValue
    parties: list[ExtractedValue] = Field(default_factory=list)

    effective_date: ExtractedValue
    expiry_date: ExtractedValue
    duration: ExtractedValue

    scope_of_work: ExtractedValue
    payment_terms: ExtractedValue

    termination_clauses: list[ExtractedValue] = Field(
        default_factory=list
    )
    obligations: list[ExtractedValue] = Field(
        default_factory=list
    )
    penalties: list[ExtractedValue] = Field(
        default_factory=list
    )

    dispute_resolution: ExtractedValue
    force_majeure: ExtractedValue
    governing_law: ExtractedValue

    important_dates: list[ExtractedValue] = Field(
        default_factory=list
    )