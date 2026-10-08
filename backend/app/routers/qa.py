from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.qa import QuestionRequest, QuestionResponse
from app.services.rag_service import RAGService


router = APIRouter(
    prefix="/qa",
    tags=["Question Answering"],
)


@router.post("/ask", response_model=QuestionResponse)
def ask_question(
    request: QuestionRequest,
    db: Session = Depends(get_db),
):

    try:

        rag_service = RAGService()

        result = rag_service.ask_question(
            db=db,
            document_version_id=request.document_version_id,
            question=request.question,
            top_k=request.top_k,
        )

        return result

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=f"Question answering failed: {exc}",
        )