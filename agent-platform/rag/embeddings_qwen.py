import numpy as np


class QwenEmbedder:
    def embed(self, texts: list[str]) -> np.ndarray:
        # 调用 embedding 服务，并返回二维 float32 ndarray。
        raise NotImplementedError