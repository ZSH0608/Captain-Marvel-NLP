"""稠密语义检索（Dense）。

向量编码用 sentence-transformers（BGE-M3 / bge-base-zh），检索用 numpy
余弦暴力检索（小规模够用、零额外依赖）；如需更大规模可换 FAISS。
`cosine_search` 为纯 numpy 实现，可独立测试。
"""
from __future__ import annotations

from typing import List, Optional, Sequence, Tuple

import numpy as np


def cosine_search(
    query_vec: np.ndarray, doc_matrix: np.ndarray, top_k: int = 10
) -> List[Tuple[int, float]]:
    """numpy 余弦相似度暴力检索，返回 [(doc_idx, score)] 降序。"""
    if doc_matrix.size == 0:
        return []
    q = np.asarray(query_vec, dtype="float32")
    D = np.asarray(doc_matrix, dtype="float32")
    q = q / (np.linalg.norm(q) + 1e-9)
    D = D / (np.linalg.norm(D, axis=1, keepdims=True) + 1e-9)
    sims = D @ q
    order = np.argsort(-sims)[:top_k]
    return [(int(i), float(sims[i])) for i in order]


class DenseRetriever:
    """sentence-transformers 编码 + numpy 检索。"""

    def __init__(self, model_name: str = "BAAI/bge-m3", device: str = "cpu") -> None:
        self.model_name = model_name
        self.device = device
        self._model = None
        self._vectors: Optional[np.ndarray] = None

    def _load_model(self) -> None:
        from sentence_transformers import SentenceTransformer  # 延迟导入

        self._model = SentenceTransformer(self.model_name, device=self.device)

    def encode(
        self,
        texts: Sequence[str],
        batch_size: int = 32,
        show_progress: bool = False,
    ) -> np.ndarray:
        if self._model is None:
            self._load_model()
        return self._model.encode(
            list(texts),
            batch_size=batch_size,
            show_progress_bar=show_progress,
            normalize_embeddings=True,
        )

    def index(self, vectors: np.ndarray) -> None:
        self._vectors = np.asarray(vectors, dtype="float32")

    def search(self, query_vec: np.ndarray, top_k: int = 10) -> List[Tuple[int, float]]:
        if self._vectors is None:
            return []
        return cosine_search(np.asarray(query_vec, dtype="float32"), self._vectors, top_k)
