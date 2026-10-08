from app.services.hybrid_search_service import (
    HybridSearchService,
)


VERSION_ID = (
    "c1e562d6-82e0-49f6-85b8-0857923d70be"
)


def main():

    service = HybridSearchService()

    query = "termination of contract"

    results = service.search(
        document_version_id=VERSION_ID,
        query=query,
        top_k=5,
    )

    print("\nHYBRID SEARCH RESULTS")
    print("=" * 80)

    for rank, result in enumerate(
        results,
        start=1,
    ):

        print(f"\nRank: {rank}")

        print(
            f"Chunk: "
            f"{result['chunk_index']}"
        )

        print(
            f"Pages: "
            f"{result['start_page']}-"
            f"{result['end_page']}"
        )

        print(
            f"RRF Score: "
            f"{result['rrf_score']:.6f}"
        )

        print(
            f"FAISS Score: "
            f"{result.get('similarity_score', 'NOT PRESENT')}"
        )

        print(
            f"BM25 Score: "
            f"{result.get('bm25_score', 'NOT PRESENT')}"
        )

        print(
            f"Text: "
            f"{result['text'][:300]}"
        )

        print("-" * 80)


if __name__ == "__main__":
    main()