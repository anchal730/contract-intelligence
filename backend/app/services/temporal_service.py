from temporalio.client import Client

from app.workflows.document_workflow import DocumentProcessingWorkflow


TEMPORAL_ADDRESS = "localhost:7233"
TASK_QUEUE = "document-processing"


async def start_document_workflow(
    document_id: str,
    version_id: str,
):
    client = await Client.connect(TEMPORAL_ADDRESS)

    workflow_id = f"document-processing-{version_id}"

    handle = await client.start_workflow(
        DocumentProcessingWorkflow.run,
        args=[document_id, version_id],
        id=workflow_id,
        task_queue=TASK_QUEUE,
    )

    return {
        "workflow_id": handle.id,
        "run_id": handle.result_run_id,
    }