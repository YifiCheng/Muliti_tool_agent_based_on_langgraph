import hashlib
from typing import Protocol

import numpy as np


class Embedder(Protocol):
    def embed(self, texts: list[str]) -> np.ndarray:
        ...


class HashEmbedder:
    """Deterministic offline embedder for tests and smoke checks."""

    def __init__(self, dimension: int = 64) -> None:
        if dimension <= 0:
            raise ValueError("dimension must be positive")
        self.dimension = dimension

    def embed(self, texts: list[str]) -> np.ndarray:
        vectors = []
        for text in texts:
            vector = np.zeros(self.dimension, dtype=np.float32)
            for token in text.lower().split():
                digest = hashlib.sha256(token.encode("utf-8")).digest()
                index = int.from_bytes(digest[:4], "little") % self.dimension
                vector[index] += 1.0
            vectors.append(vector)

        if not vectors:
            return np.empty((0, self.dimension), dtype=np.float32)
        return np.stack(vectors)


def build_embedder(provider: str = "hash") -> Embedder:
    if provider == "hash":
        return HashEmbedder()
    raise ValueError(f"Unsupported embedder provider: {provider}")