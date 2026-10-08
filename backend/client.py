import asyncio

from temporalio.client import Client

from app.workflows.document_workflow import DocumentProcessingWorkflow


async def main():
    client = await Client.connect("localhost:7233")

    result = await client.execute_workflow(
        DocumentProcessingWorkflow.run,
        args=[
            "test-document-001",
            "test-version-001",
        ],
        id="document-processing-test-002",
        task_queue="document-processing",
    )

    print("Workflow result:")
    print(result)


if __name__ == "__main__":
    asyncio.run(main())