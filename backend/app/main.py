from fastapi import FastAPI

from app.api.documents import router as documents_router
from app.routers.search import router as search_router
from app.routers.qa import router as qa_router
from app.routers.contract_extraction import router as contract_extraction_router
from app.routers.contract_risk import router as contract_risk_router
from app.routers.contract_summary import router as contract_summary_router


app = FastAPI(
    title="AI Contract Intelligence Platform",
    version="0.1.0",
)


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "contract-intelligence-api",
    }


app.include_router(documents_router)
app.include_router(search_router)
app.include_router(qa_router)
app.include_router(contract_extraction_router)
app.include_router(contract_risk_router)
app.include_router(contract_summary_router)