import os

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate

from app.services.hybrid_search_service import HybridSearchService
from app.services.reranker_service import RerankerService


load_dotenv()


class RAGService:

    def __init__(self):

        # ----------------------------------
        # Hybrid retrieval
        # FAISS + BM25 + RRF
        # ----------------------------------

        self.hybrid_search = HybridSearchService()

        # ----------------------------------
        # Cross-encoder re-ranking
        # ----------------------------------

        self.reranker = RerankerService()

        # ----------------------------------
        # Groq LLM
        # ----------------------------------

        self.llm = ChatGroq(
            model="openai/gpt-oss-120b",
            temperature=0,
            api_key=os.getenv("GROQ_API_KEY"),
        )

        # ----------------------------------
        # RAG Prompt
        # ----------------------------------

        self.prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """
You are a contract intelligence assistant.

Answer the user's question ONLY using the
provided contract context.

Rules:

1. Do not invent information.
2. Do not use outside knowledge.
3. If the answer is not present in the
   provided context, say that the information
   is not available in the provided contract.
4. Mention the relevant page number when possible.
5. Keep the answer clear and concise.
6. When multiple clauses are relevant,
   explain them separately.
7. Do not generalize a condition from one clause
   to other clauses. Clearly distinguish which
   termination conditions, notice periods,
   penalties, or rights belong to which clause.
8. When different clauses describe different
   termination mechanisms, report them separately
   and do not combine their requirements unless
   the contract explicitly connects them.
""",
                ),
                (
                    "human",
                    """
Contract context:

{context}

Question:

{question}
""",
                ),
            ]
        )

    def ask_question(
        self,
        db,
        document_version_id: str,
        question: str,
        top_k: int = 5,
    ):

        # ----------------------------------
        # 1. Hybrid Retrieval
        # ----------------------------------

        search_results = self.hybrid_search.search(
            document_version_id=document_version_id,
            query=question,
            top_k=max(top_k * 2, 10),
        )

        # ----------------------------------
        # 2. Re-ranking
        # ----------------------------------

        search_results = self.reranker.rerank(
            query=question,
            results=search_results,
            top_k=top_k,
        )

        # ----------------------------------
        # 3. No Relevant Results
        # ----------------------------------

        if not search_results:

            return {
                "answer": (
                    "The information is not available "
                    "in the provided contract."
                ),
                "sources": [],
            }

        # ----------------------------------
        # 4. Build Contract Context
        # ----------------------------------

        context_parts = []

        for result in search_results:

            context_parts.append(
                f"""
Chunk {result['chunk_index']}
Page {result['start_page']}-{result['end_page']}

{result['text']}
"""
            )

        context = "\n\n".join(context_parts)

        # ----------------------------------
        # 5. Send Context to LLM
        # ----------------------------------

        messages = self.prompt.format_messages(
            context=context,
            question=question,
        )

        response = self.llm.invoke(messages)

        # ----------------------------------
        # 6. Prepare Sources
        # ----------------------------------

        sources = []

        for result in search_results:

            sources.append(
                {
                    "chunk_index": result["chunk_index"],
                    "start_page": result["start_page"],
                    "end_page": result["end_page"],

                    # Actual retrieved contract text
                    "text": result.get("text", ""),

                    "rrf_score": float(
                        result.get(
                            "rrf_score",
                            0.0,
                        )
                    ),

                    "reranker_score": float(
                        result.get(
                            "reranker_score",
                            0.0,
                        )
                    ),
                }
            )

        # ----------------------------------
        # 7. Return Final Response
        # ----------------------------------

        return {
            "answer": response.content,
            "sources": sources,
        }