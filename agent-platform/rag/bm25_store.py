import re

from rank_bm25 import BM25Okapi

from rag.models import DocumentChunk, RetrievalResult


def tokenize(text: str) -> list[str]:
    chinese_chars = re.findall(r"[\u4e00-\u9fff]", text)
    chinese_bigrams = [
        "".join(chinese_chars[index : index + 2])
        for index in range(len(chinese_chars) - 1)
    ]
    words = re.findall(r"[A-Za-z0-9_]+", text.lower())
    return chinese_chars + chinese_bigrams + words


class BM25Store:
    def __init__(self, chunks: list[DocumentChunk]) -> None:
        if not chunks:
            raise ValueError("BM25Store requires at least one chunk")
        self.chunks = chunks
        self.tokens = [tokenize(chunk.content) for chunk in chunks]
        self.index = BM25Okapi(self.tokens)

    def search(self, query: str, top_k: int = 5) -> list[RetrievalResult]:
        query_tokens = tokenize(query)
        if not query_tokens:
            return []

        raw_scores = self.index.get_scores(query_tokens)
        query_token_set = set(query_tokens)
        ranked_indices = sorted(
            range(len(raw_scores)),
            key=lambda index: (
                raw_scores[index],
                len(query_token_set.intersection(self.tokens[index])),
            ),
            reverse=True,
        )

        results: list[RetrievalResult] = []
        for index in ranked_indices[:top_k]:
            overlap = len(query_token_set.intersection(self.tokens[index]))
            if raw_scores[index] <= 0 and overlap == 0:
                continue
            results.append(
                RetrievalResult(
                    chunk=self.chunks[index],
                    score=float(raw_scores[index] if raw_scores[index] > 0 else overlap),
                    retriever="bm25",
                )
            )
        return results
