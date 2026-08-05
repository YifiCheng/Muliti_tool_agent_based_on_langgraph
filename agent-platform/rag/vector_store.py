from typing import Protocol

import numpy as np

from rag.models import DocumentChunk, RetrievalResult


class Embedder(Protocol):
    def embed(self, texts: list[str]) -> np.ndarray:
        ...


class VectorStore:
    def __init__(self, chunks: list[DocumentChunk], embedder: Embedder) -> None:
        if not chunks:
            raise ValueError("VectorStore requires at least one chunk")
        self.chunks = chunks
        self.embedder = embedder
        self.vectors = self._normalize(embedder.embed([chunk.content for chunk in chunks]))

    def search(self, query: str, top_k: int = 5) -> list[RetrievalResult]:
        query_vector = self._normalize(self.embedder.embed([query]))[0]
        scores = self.vectors @ query_vector
        ranked_indices = np.argsort(scores)[::-1][:top_k]

        results: list[RetrievalResult] = []
        for index in ranked_indices:
            score = float(scores[index])
            if score <= 0:
                continue
            results.append(
                RetrievalResult(
                    chunk=self.chunks[int(index)],
                    score=score,
                    retriever="vector",
                )
            )
        return results

    @staticmethod
    def _normalize(vectors: np.ndarray) -> np.ndarray:
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        return vectors / np.maximum(norms, 1e-12)
