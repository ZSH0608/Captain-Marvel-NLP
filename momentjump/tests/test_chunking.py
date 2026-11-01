import pytest

from src.ingest.chunking import (
    chunk,
    chunk_fixed,
    chunk_pause_punctuation,
    chunk_sliding,
)
from src.segment import TimedText


def make_items(n: int = 10, step: float = 3.0):
    return [TimedText(i * step, i * step + 2.8, f"第{i}句内容。") for i in range(n)]


def test_chunk_fixed_nonempty():
    chunks = chunk_fixed(make_items(), window_sec=9.0)
    assert len(chunks) >= 1
    assert all(c.start < c.end for c in chunks)


def test_chunk_fixed_merges():
    # 3 秒/句，9 秒窗口 → 约每 3 句一段，10 句至少 3 段
    chunks = chunk_fixed(make_items(), window_sec=9.0)
    assert len(chunks) >= 3


def test_chunk_sliding_overlap():
    chunks = chunk_sliding(make_items(), window_sec=9.0, step_sec=6.0)
    assert len(chunks) > 1
    # 滑动窗有重叠：相邻 chunk 起点间隔 = step_sec
    starts = [c.start for c in chunks]
    assert starts[1] - starts[0] == 6.0


def test_chunk_pause_punctuation():
    chunks = chunk_pause_punctuation(make_items(), min_sec=6.0, max_sec=12.0)
    assert len(chunks) >= 1
    # 每段文本以句号结尾（首段之后均以句末标点结束）
    assert all(c.text.rstrip().endswith("。") for c in chunks)


def test_chunk_dispatch():
    items = make_items()
    for strat in ("fixed", "sliding", "pause_punctuation"):
        assert len(chunk(items, strat)) > 0


def test_chunk_unknown_strategy():
    with pytest.raises(ValueError):
        chunk(make_items(), "nope")
