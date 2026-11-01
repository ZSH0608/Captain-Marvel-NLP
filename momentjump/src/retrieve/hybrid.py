"""Hybrid 检索：Dense + BM25 的 RRF（Reciprocal Rank Fusion）融合。"""
from __future__ import annotations

from typing import Dict, List, Sequence, Tuple


def reciprocal_rank_fusion(
    ranked_lists: Sequence[Sequence], k: int = 60
) -> List[Tuple[object, float]]:
    """RRF 融合多个排序列表。

    每个列表的元素是 doc_id，按 rank 从 1 开始贡献 1/(k+rank)。
    返回按融合分降序的 [(doc_id, score)]。
    """
    scores: Dict[object, float] = {}
    for ranked in ranked_lists:
        for rank, doc_id in enumerate(ranked, start=1):
            scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + rank)
    return sorted(scores.items(), key=lambda kv: kv[1], reverse=True)


def weighted_fusion(
    dense_scores: Sequence[Tuple[object, float]],
    bm25_scores: Sequence[Tuple[object, float]],
    alpha: float = 0.5,
) -> List[Tuple[object, float]]:
    """线性加权融合（各通道分数需先做归一化）。alpha 为 Dense 通道权重。"""
    merged: Dict[object, float] = {}
    for doc_id, s in dense_scores:
        merged[doc_id] = merged.get(doc_id, 0.0) + alpha * s
    for doc_id, s in bm25_scores:
        merged[doc_id] = merged.get(doc_id, 0.0) + (1 - alpha) * s
    return sorted(merged.items(), key=lambda kv: kv[1], reverse=True)
