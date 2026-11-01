"""检索评测指标：R@K、mIoU、时间误差（对应方案 §9）。

命中规则：预测片段与 gold 区间 IoU ≥ θ，或预测中心点落入 gold ± δ。
"""
from __future__ import annotations

import statistics
from typing import Sequence, Tuple

Span = Tuple[float, float]


def span_iou(pred: Span, gold: Span) -> float:
    """两个时间区间的交并比 IoU。"""
    ps, pe = pred
    gs, ge = gold
    inter = max(0.0, min(pe, ge) - max(ps, gs))
    union = (pe - ps) + (ge - gs) - inter
    if union <= 0:
        return 0.0
    return inter / union


def is_hit(pred: Span, gold: Span, delta: float = 10.0, iou_thresh: float = 0.3) -> bool:
    """命中判定：IoU ≥ iou_thresh 或预测中心点落入 gold ± delta。"""
    if span_iou(pred, gold) >= iou_thresh:
        return True
    pc = (pred[0] + pred[1]) / 2.0
    gc = (gold[0] + gold[1]) / 2.0
    return abs(pc - gc) <= delta


def recall_at_k(
    preds: Sequence[Sequence[Span]],
    golds: Sequence[Span],
    k: int,
    delta: float = 10.0,
    iou_thresh: float = 0.3,
) -> float:
    """R@K：Top-K 中任一命中即算命中，返回命中比例（0~1）。

    preds[i] 是第 i 条 query 返回的 Top-K 片段列表；golds[i] 是对应真实区间。
    """
    assert len(preds) == len(golds), "preds 与 golds 长度必须一致"
    if not preds:
        return 0.0
    hits = 0
    for topk, g in zip(preds, golds):
        if any(is_hit(p, g, delta, iou_thresh) for p in topk[:k]):
            hits += 1
    return hits / len(preds)


def median_time_error(preds: Sequence[Span], golds: Sequence[Span]) -> float:
    """预测起点与 gold 起点的 |Δ| 中位数（单位：秒）。"""
    errs = [abs(p[0] - g[0]) for p, g in zip(preds, golds)]
    return float(statistics.median(errs)) if errs else float("nan")


def mean_iou(preds: Sequence[Span], golds: Sequence[Span]) -> float:
    """平均 IoU。"""
    ious = [span_iou(p, g) for p, g in zip(preds, golds)]
    return sum(ious) / len(ious) if ious else float("nan")
