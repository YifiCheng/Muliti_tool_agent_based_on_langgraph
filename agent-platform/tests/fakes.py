import numpy as np


class FakeEmbedder:
    def __init__(self, mapping: dict[str, list[float]]) -> None:
        self.mapping = mapping

    def embed(self, texts: list[str]) -> np.ndarray:
        return np.array(
            [self.mapping.get(text, [0.0, 0.0, 1.0]) for text in texts],
            dtype=np.float32,
        )