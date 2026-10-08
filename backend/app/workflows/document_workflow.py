from datetime import timedelta

from temporalio import workflow


with workflow.unsafe.imports_passed_through():
    pass


@workflow.defn
class DocumentProcessingWorkflow:

    @workflow.run
    async def run(
        self,
        document_id: str,
        version_id: str,
    ) -> str:

        # 1. Process PDF, OCR and create chunks
        processing_result = await workflow.execute_activity(
            "process_document",
            args=[
                document_id,
                version_id,
            ],
            start_to_close_timeout=timedelta(
                minutes=5
            ),
        )

        # 2. Build semantic search index
        faiss_result = await workflow.execute_activity(
            "build_faiss_index",
            args=[
                version_id
            ],
            start_to_close_timeout=timedelta(
                minutes=10
            ),
        )

        # 3. Build keyword search index
        bm25_result = await workflow.execute_activity(
            "build_bm25_index",
            args=[
                version_id
            ],
            start_to_close_timeout=timedelta(
                minutes=5
            ),
        )

        return (
            "Document processing completed. "
            f"FAISS indexing completed: {faiss_result}. "
            f"BM25 indexing completed: {bm25_result}"
        )