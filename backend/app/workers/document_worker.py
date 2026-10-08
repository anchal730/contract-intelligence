import asyncio
from concurrent.futures import ThreadPoolExecutor

from temporalio.client import Client
from temporalio.worker import Worker

from app.workflows.document_workflow import DocumentProcessingWorkflow

from app.workflows.activities import (
    process_document,
    build_faiss_index,
    build_bm25_index,
)


async def main():
    client = await Client.connect("localhost:7233")

    activity_executor = ThreadPoolExecutor(
        max_workers=4
    )

    worker = Worker(
        client,
        task_queue="document-processing",
        workflows=[DocumentProcessingWorkflow],
        activities=[
            process_document,
            build_faiss_index,
            build_bm25_index,
        ],
        activity_executor=activity_executor,
    )

    print("Document worker started")

    try:
        await worker.run()

    finally:
        activity_executor.shutdown(
            wait=True
        )


if __name__ == "__main__":
    asyncio.run(main())