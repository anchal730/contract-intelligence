from pydantic import BaseModel, Field


class QuestionRequest(BaseModel):

    document_version_id: str

    question: str = Field(
        min_length=1
    )

    top_k: int = Field(
        default=5,
        ge=1,
        le=20,
    )


class Source(BaseModel):

    chunk_index: int

    start_page: int

    end_page: int
    
    text: str

    rrf_score: float

    reranker_score: float


class QuestionResponse(BaseModel):

    answer: str

    sources: list[Source]