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


def _resolve_local_snapshot(model_name: str) -> str:
    """把 HF 模型名解析为本地缓存快照路径（离线可用）；找不到则原样返回模型名。

    兜底多个候选缓存根，并选取「含 config.json + 权重文件」的完整快照，
    避免 HF 缓存存在多个不完整 snapshot 时加载失败。
    """
    import os

    cache_name = "models--" + model_name.replace("/", "--")
    candidates = []
    hf_home = os.environ.get("HF_HOME")
    if hf_home:
        candidates.append(os.path.join(hf_home, cache_name))
        candidates.append(os.path.join(hf_home, "hub", cache_name))
    candidates.append(
        os.path.join(os.path.expanduser("~"), ".cache", "huggingface", "hub", cache_name)
    )

    for base in candidates:
        snap_dir = os.path.join(base, "snapshots")
        if not os.path.isdir(snap_dir):
            continue
        for rev in sorted(os.listdir(snap_dir)):
            p = os.path.join(snap_dir, rev)
            has_cfg = os.path.exists(os.path.join(p, "config.json"))
            has_weights = os.path.exists(os.path.join(p, "pytorch_model.bin")) or os.path.exists(
                os.path.join(p, "model.safetensors")
            )
            if has_cfg and has_weights:
                return p
    return model_name


class DenseRetriever:
    """sentence-transformers 编码 + numpy 检索。"""

    def __init__(self, model_name: str = "BAAI/bge-base-zh-v1.5", device: str = "cpu") -> None:
        self.model_name = model_name
        self.device = device
        self._model = None
        self._vectors: Optional[np.ndarray] = None

    def _load_model(self) -> None:
        import os  # 模型已缓存于本地，强制离线，避免联网重查

        os.environ.setdefault("HF_HUB_OFFLINE", "1")
        os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
        from sentence_transformers import SentenceTransformer  # 延迟导入

        # 离线场景：优先用本地缓存快照路径，避免 HF 缓存不完整导致加载失败
        local = _resolve_local_snapshot(self.model_name)
        self._model = SentenceTransformer(local, device=self.device)

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
