"""索引构建与持久化：向量(numpy) + BM25 + 元数据。

规模小用 numpy + rank_bm25 + JSON 即可；如需更大规模可换 FAISS / sqlite。
"""
from __future__ import annotations

import json
import os
from typing import List, Optional, Sequence

import numpy as np

from ..retrieve.bm25 import BM25Retriever
from ..segment import Segment


class IndexStore:
    """统一索引存储（类别无关），检索层只依赖它的 segments / vectors / bm25。"""

    def __init__(self) -> None:
        self.segments: List[Segment] = []
        self.vectors: Optional[np.ndarray] = None
        self.bm25: Optional[BM25Retriever] = None

    @classmethod
    def build(cls, segments: Sequence[Segment], vectors: Optional[np.ndarray] = None) -> "IndexStore":
        store = cls()
        store.segments = list(segments)
        store.vectors = (
            np.asarray(vectors, dtype="float32") if vectors is not None and len(vectors) else None
        )
        store.bm25 = BM25Retriever([s.text for s in store.segments])
        return store

    def save(self, dirpath: str) -> None:
        os.makedirs(dirpath, exist_ok=True)
        with open(os.path.join(dirpath, "segments.json"), "w", encoding="utf-8") as f:
            json.dump([s.to_dict() for s in self.segments], f, ensure_ascii=False, indent=2)
        if self.vectors is not None:
            np.save(os.path.join(dirpath, "vectors.npy"), self.vectors)

    @classmethod
    def load(cls, dirpath: str) -> "IndexStore":
        seg_path = os.path.join(dirpath, "segments.json")
        with open(seg_path, encoding="utf-8") as f:
            segments = [Segment.from_dict(d) for d in json.load(f)]
        vec_path = os.path.join(dirpath, "vectors.npy")
        vectors = np.load(vec_path) if os.path.exists(vec_path) else None
        return cls.build(segments, vectors)
