from pathlib import Path
import json

import faiss
import numpy as np
from sqlalchemy.orm import Session

from app.models.document import DocumentChunk
from app.services.embedding_service import EmbeddingService


# Directory for storing FAISS indexes
FAISS_STORAGE_DIR = Path("storage/faiss")

FAISS_STORAGE_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


class FAISSService:

    def __init__(self):

        self.embedding_service = EmbeddingService()

    def build_index(
        self,
        db: Session,
        document_version_id: str,
    ) -> dict:

        # 1. Fetch document chunks
        chunks = (
            db.query(DocumentChunk)
            .filter(
                DocumentChunk.document_version_id
                == document_version_id
            )
            .order_by(
                DocumentChunk.chunk_index
            )
            .all()
        )

        if not chunks:
            raise ValueError(
                "No chunks found for this document version"
            )

        # 2. Extract chunk texts
        texts = [
            chunk.text
            for chunk in chunks
            if chunk.text and chunk.text.strip()
        ]

        if not texts:
            raise ValueError(
                "Chunks contain no usable text"
            )

        # 3. Generate embeddings
        embeddings = (
            self.embedding_service.generate_embeddings(
                texts
            )
        )

        # 4. Convert embeddings to NumPy array
        embedding_array = np.array(
            embeddings,
            dtype="float32",
        )

        # 5. Create FAISS index
        dimension = embedding_array.shape[1]

        index = faiss.IndexFlatIP(dimension)

        # 6. Add vectors
        index.add(embedding_array)

        # 7. Define storage paths
        index_path = (
            FAISS_STORAGE_DIR
            / f"{document_version_id}.index"
        )

        metadata_path = (
            FAISS_STORAGE_DIR
            / f"{document_version_id}.json"
        )

        # 8. Save FAISS index
        faiss.write_index(
            index,
            str(index_path),
        )

        # 9. Save metadata
        metadata = []

        valid_chunks = [
            
            chunk
            for chunk in chunks
            if chunk.text and chunk.text.strip()
        ]

        for chunk in valid_chunks:
            

            metadata.append(
                {
                    "chunk_id": chunk.id,
                    "chunk_index": chunk.chunk_index,
                    "document_version_id": (
                        chunk.document_version_id
                    ),
                    "text": chunk.text,
                    "start_page": chunk.start_page,
                    "end_page": chunk.end_page,
                }
            )

        with open(
            metadata_path,
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                metadata,
                file,
                ensure_ascii=False,
                indent=2,
            )

        return {
            "document_version_id": document_version_id,
            "chunk_count": len(metadata),
            "embedding_dimension": dimension,
            "index_path": str(index_path),
            "metadata_path": str(metadata_path),
        }

    def search(
        self,
        document_version_id: str,
        query: str,
        top_k: int = 5,
    ) -> list[dict]:

        if not query or not query.strip():
            raise ValueError(
                "Query cannot be empty"
            )

        index_path = (
            FAISS_STORAGE_DIR
            / f"{document_version_id}.index"
        )

        metadata_path = (
            FAISS_STORAGE_DIR
            / f"{document_version_id}.json"
        )

        # 1. Check whether index exists
        if not index_path.exists():
            raise FileNotFoundError(
                "FAISS index not found. Build the index first."
            )

        if not metadata_path.exists():
            raise FileNotFoundError(
                "FAISS metadata not found."
            )

        # 2. Load FAISS index
        index = faiss.read_index(
            str(index_path)
        )

        # 3. Load metadata
        with open(
            metadata_path,
            "r",
            encoding="utf-8",
        ) as file:

            metadata = json.load(file)

        # 4. Generate query embedding
        query_embedding = (
            self.embedding_service.generate_embedding(
                query
            )
        )

        query_array = np.array(
            [query_embedding],
            dtype="float32",
        )

        # 5. Limit top_k to available records
        search_k = min(
            top_k,
            index.ntotal,
        )

        if search_k == 0:
            return []

        # 6. Search similar vectors
        scores, indices = index.search(
            query_array,
            search_k,
        )

        results = []

        for score, index_position in zip(
            scores[0],
            indices[0],
        ):

            if index_position < 0:
                continue

            result = metadata[index_position].copy()

            result["similarity_score"] = float(
                score
            )

            results.append(result)

        return results