from rag.models import DocumentChunk, RetrievalResult


class HybridRetriever:
    def __init__(self, bm25_store, vector_store) -> None:
        self.bm25_store = bm25_store
        self.vector_store = vector_store

    def search(
        self,
        query: str,
        top_k: int = 5,
        *,
        bm25_k: int | None = None,
        vector_k: int | None = None,
    ) -> list[RetrievalResult]:
        bm25_results = self.bm25_store.search(query, top_k=bm25_k or top_k)
        vector_results = self.vector_store.search(query, top_k=vector_k or top_k)

        fused: dict[str, dict] = {}
        rank_constant = 60

        for rank, result in enumerate(bm25_results, start=1):
            item = fused.setdefault(result.chunk.chunk_id, {"result": result, "score": 0.0})
            item["score"] += 1.0 / (rank_constant + rank)

        for rank, result in enumerate(vector_results, start=1):
            item = fused.setdefault(result.chunk.chunk_id, {"result": result, "score": 0.0})
            item["score"] += 1.0 / (rank_constant + rank)

        ranked = sorted(fused.values(), key=lambda item: item["score"], reverse=True)
        output: list[RetrievalResult] = []
        for item in ranked[:top_k]:
            result = item["result"]
            output.append(
                RetrievalResult(
                    chunk=result.chunk,
                    score=float(item["score"]),
                    retriever="hybrid",
                )
            )
        return output