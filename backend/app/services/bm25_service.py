import json
from pathlib import Path

from rank_bm25 import BM25Okapi


BM25_STORAGE_DIR = Path("storage/bm25")
BM25_STORAGE_DIR.mkdir(parents=True, exist_ok=True)


class BM25Service:

    def __init__(self):
        pass

    def build_index(
        self,
        chunks: list[dict],
        document_version_id: str,
    ) -> dict:

        if not chunks:
            raise ValueError("No chunks provided")

        valid_chunks = [
            chunk
            for chunk in chunks
            if chunk.get("text") and chunk["text"].strip()
        ]

        if not valid_chunks:
            raise ValueError("No valid chunks available")

        metadata = []

        tokenized_documents = []

        for chunk in valid_chunks:

            text = chunk["text"].strip()

            tokenized_documents.append(
                text.lower().split()
            )

            metadata.append({
                "chunk_index": chunk["chunk_index"],
                "text": text,
                "start_page": chunk["start_page"],
                "end_page": chunk["end_page"],
            })

        # BM25 itself is recreated from the metadata
        # when searching. We persist the tokenized corpus.
        index_data = {
            "document_version_id": document_version_id,
            "documents": tokenized_documents,
            "metadata": metadata,
        }

        json_path = (
            BM25_STORAGE_DIR
            / f"{document_version_id}.json"
        )

        with open(
            json_path,
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                index_data,
                file,
                ensure_ascii=False,
            )

        return {
            "document_version_id": document_version_id,
            "chunk_count": len(valid_chunks),
            "path": str(json_path),
        }

    def search(
        self,
        document_version_id: str,
        query: str,
        top_k: int = 5,
    ) -> list[dict]:

        if not query or not query.strip():
            return []

        json_path = (
            BM25_STORAGE_DIR
            / f"{document_version_id}.json"
        )

        if not json_path.exists():

            raise FileNotFoundError(
                f"BM25 index not found: {json_path}"
            )

        with open(
            json_path,
            "r",
            encoding="utf-8",
        ) as file:

            index_data = json.load(file)

        documents = index_data["documents"]
        metadata = index_data["metadata"]

        bm25 = BM25Okapi(documents)

        tokenized_query = query.lower().split()

        scores = bm25.get_scores(
            tokenized_query
        )

        ranked_indexes = sorted(
            range(len(scores)),
            key=lambda i: scores[i],
            reverse=True,
        )[:top_k]

        results = []

        for index in ranked_indexes:

            result = metadata[index].copy()

            result["bm25_score"] = float(
                scores[index]
            )

            results.append(result)

        return results