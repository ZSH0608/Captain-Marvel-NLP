"""BM25 关键词检索（Hybrid 的关键词通道）。

讲解型 query 绝大多数是知识点专有名词，BM25 是主力；剧情型则必须配合
场景级语义检索（见 retrieve/dense.py + ingest/chunking.py 的场景聚合）。
"""
from __future__ import annotations

import re
from typing import Callable, List, Optional, Sequence, Tuple

from rank_bm25 import BM25Okapi


def default_tokenize(text: str) -> List[str]:
    """默认分词：优先 jieba（中文），失败则回退到正则切分。"""
    try:
        import jieba  # type: ignore

        return [w for w in jieba.lcut(text.lower()) if w.strip()]
    except ImportError:
        return [
            w
            for w in re.findall(r"[一-鿿]+|[a-zA-Z0-9]+", text.lower())
            if w.strip()
        ]


class BM25Retriever:
    """封装 rank_bm25，提供 search(query, top_k) -> [(doc_idx, score)]。"""

    def __init__(
        self,
        docs: Sequence[str],
        tokenizer: Optional[Callable[[str], List[str]]] = None,
    ) -> None:
        self.tokenizer = tokenizer or default_tokenize
        self.docs: List[str] = list(docs)
        self._tokenized = [self.tokenizer(d) for d in self.docs]
        self._bm25 = BM25Okapi(self._tokenized) if self._tokenized else None

    def search(self, query: str, top_k: int = 10) -> List[Tuple[int, float]]:
        """返回 Top-K 的 [(doc_idx, score)]，按分数降序。"""
        if self._bm25 is None or top_k <= 0:
            return []
        qt = self.tokenizer(query)
        scores = self._bm25.get_scores(qt)
        order = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
        return [(i, float(scores[i])) for i in order]
