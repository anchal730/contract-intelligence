from app.services.bm25_service import BM25Service


VERSION_ID = "c1e562d6-82e0-49f6-85b8-0857923d70be"


def main():

    service = BM25Service()

    results = service.search(
        document_version_id=VERSION_ID,
        query="termination of contract",
        top_k=5,
    )

    print("\nBM25 SEARCH RESULTS\n")

    for result in results:

        print(
            f"Chunk: {result['chunk_index']}"
        )

        print(
            f"Pages: "
            f"{result['start_page']}-"
            f"{result['end_page']}"
        )

        print(
            f"Score: "
            f"{result['bm25_score']}"
        )

        print(
            f"Text: "
            f"{result['text'][:300]}"
        )

        print("-" * 80)


if __name__ == "__main__":
    main()