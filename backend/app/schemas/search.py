from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    document_version_id: str
    query: str = Field(min_length=1)
    top_k: int = Field(default=5, ge=1, le=20)


class SearchResult(BaseModel):
    chunk_index: int
    text: str
    start_page: int
    end_page: int
    similarity_score: float