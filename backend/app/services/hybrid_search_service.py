from app.services.faiss_service import FAISSService
from app.services.bm25_service import BM25Service


class HybridSearchService:

    def __init__(self):
        self.faiss_service = FAISSService()
        self.bm25_service = BM25Service()

    def search(
        self,
        document_version_id: str,
        query: str,
        top_k: int = 5,
    ) -> list[dict]:

        candidate_k = max(top_k * 2, 10)

        # -----------------------------------
        # 1. FAISS search
        # -----------------------------------

        semantic_results = self.faiss_service.search(
            document_version_id=document_version_id,
            query=query,
            top_k=candidate_k,
        )

        # -----------------------------------
        # 2. BM25 search
        # -----------------------------------

        keyword_results = self.bm25_service.search(
            document_version_id=document_version_id,
            query=query,
            top_k=candidate_k,
        )

        # -----------------------------------
        # 3. Store results by chunk
        # -----------------------------------

        result_map = {}
        rrf_scores = {}

        k = 60

        # FAISS results
        for rank, result in enumerate(
            semantic_results,
            start=1,
        ):

            chunk_index = result["chunk_index"]

            rrf_scores[chunk_index] = (
                rrf_scores.get(chunk_index, 0.0)
                + 1.0 / (k + rank)
            )

            result_map.setdefault(
                chunk_index,
                {}
            )

            result_map[chunk_index].update({
                "chunk_index": chunk_index,
                "text": result["text"],
                "start_page": result["start_page"],
                "end_page": result["end_page"],
                "similarity_score": result.get(
                    "similarity_score",
                    0.0,
                ),
            })

        # BM25 results
        for rank, result in enumerate(
            keyword_results,
            start=1,
        ):

            chunk_index = result["chunk_index"]

            rrf_scores[chunk_index] = (
                rrf_scores.get(chunk_index, 0.0)
                + 1.0 / (k + rank)
            )

            result_map.setdefault(
                chunk_index,
                {}
            )

            result_map[chunk_index].update({
                "chunk_index": chunk_index,
                "text": result["text"],
                "start_page": result["start_page"],
                "end_page": result["end_page"],
                "bm25_score": result.get(
                    "bm25_score",
                    0.0,
                ),
            })

        # -----------------------------------
        # 4. Rank using RRF
        # -----------------------------------

        ranked_chunks = sorted(
            rrf_scores.items(),
            key=lambda item: item[1],
            reverse=True,
        )

        # -----------------------------------
        # 5. Build final results
        # -----------------------------------

        final_results = []

        for chunk_index, rrf_score in ranked_chunks[:top_k]:

            result = result_map[chunk_index].copy()

            result["rrf_score"] = float(
                rrf_score
            )

            # Ensure both fields always exist
            result.setdefault(
                "similarity_score",
                0.0,
            )

            result.setdefault(
                "bm25_score",
                0.0,
            )

            final_results.append(result)

        return final_results