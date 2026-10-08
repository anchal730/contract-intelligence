from pydantic import BaseModel


class DocumentUploadResponse(BaseModel):
    document_id: str
    version_id: str
    filename: str
    file_size: int
    sha256: str
    status: str
    workflow_id: str
    workflow_run_id: str