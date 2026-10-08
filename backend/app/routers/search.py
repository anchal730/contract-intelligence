from fastapi import APIRouter, HTTPException

from app.schemas.search import SearchRequest, SearchResult
from app.services.faiss_service import FAISSService


router = APIRouter(prefix="/search", tags=["Search"])

faiss_service = FAISSService()


@router.post("/", response_model=list[SearchResult])
def search_documents(request: SearchRequest):
    try:
        results = faiss_service.search(
            document_version_id=request.document_version_id,
            query=request.query,
            top_k=request.top_k,
        )

        return results

    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="FAISS index not found for this document version",
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Search failed: {str(exc)}",
        )