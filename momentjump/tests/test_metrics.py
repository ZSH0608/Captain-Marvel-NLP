import pytest

from src.eval.metrics import (
    is_hit,
    mean_iou,
    median_time_error,
    recall_at_k,
    span_iou,
)


def test_span_iou():
    assert span_iou((0, 10), (0, 10)) == 1.0
    assert span_iou((0, 5), (5, 10)) == 0.0
    assert span_iou((0, 10), (5, 10)) == 0.5


def test_is_hit():
    assert is_hit((0, 10), (0, 10))
    # 中心 7 vs 5，|Δ|=2 <= delta=5
    assert is_hit((2, 12), (0, 10), delta=5.0)


def test_recall_at_k():
    preds = [[(0, 10)], [(20, 30), (0, 10)]]
    golds = [(0, 10), (0, 10)]
    # query1 的 Top-1 是 (20,30) 未命中，(0,10) 在 Top-2
    assert recall_at_k(preds, golds, k=1) == 0.5
    assert recall_at_k(preds, golds, k=2) == 1.0


def test_recall_at_k_miss():
    preds = [[(20, 30)]]
    golds = [(0, 10)]
    assert recall_at_k(preds, golds, k=1) == 0.0


def test_median_time_error():
    preds = [(0, 10), (5, 15)]
    golds = [(0, 10), (0, 10)]
    assert median_time_error(preds, golds) == 2.5


def test_mean_iou():
    preds = [(0, 10), (5, 15)]
    golds = [(0, 10), (0, 10)]
    # iou1=1.0, iou2=(10-5)/((10)+(10)-(5))=1/3 -> mean=2/3
    assert mean_iou(preds, golds) == pytest.approx(2 / 3)
