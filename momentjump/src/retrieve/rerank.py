"""Cross-Encoder 重排（bge-reranker-base），提高 Top-1/Top-3 精度。"""
from __future__ import annotations

from typing import List, Optional, Sequence, Tuple


class Reranker:
    """用 sentence-transformers CrossEncoder 对候选做精排。"""

    def __init__(self, model_name: str = "BAAI/bge-reranker-base") -> None:
        self.model_name = model_name
        self._model = None

    def _load_model(self) -> None:
        from sentence_transformers import CrossEncoder  # 延迟导入

        self._model = CrossEncoder(self.model_name)

    def rerank(
        self,
        query: str,
        docs: Sequence[str],
        top_n: Optional[int] = None,
    ) -> List[Tuple[int, float]]:
        """返回 [(doc_idx, score)] 按相关性分数降序。

        docs 为候选文本列表（通常来自 Hybrid 召回的前 N 个）。
        """
        if self._model is None:
            self._load_model()
        if not docs:
            return []
        pairs = [(query, d) for d in docs]
        scores = self._model.predict(pairs)
        order = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
        if top_n is not None:
            order = order[:top_n]
        return [(int(i), float(scores[i])) for i in order]
