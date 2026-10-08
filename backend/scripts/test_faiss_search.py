from app.services.faiss_service import FAISSService


DOCUMENT_VERSION_ID = "d59e37d1-a9e8-4052-95fc-31c30f61219b"


def main():
    service = FAISSService()

    query = "What are the termination conditions of this contract?"

    results = service.search(
        document_version_id=DOCUMENT_VERSION_ID,
        query=query,
        top_k=5,
    )

    print("\nSEARCH RESULTS")
    print("=" * 80)

    for index, result in enumerate(results, start=1):
        print(f"\nResult {index}")
        print("-" * 80)
        print(f"Chunk ID: {result['chunk_index']}")
        print(f"Pages: {result['start_page']} - {result['end_page']}")
        print(f"Similarity: {result['similarity_score']:.4f}")
        print(f"Text:\n{result['text']}")


if __name__ == "__main__":
    main()