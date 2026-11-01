"""分块策略。

讲解型视频以「停顿·标点边界」为主切分策略（贴合讲解节奏、语义完整），
固定窗 / 滑动窗作为消融基线（对应方案 §5.1 与 RQ2）。

输入：带时间戳的转录项列表（`TimedText`，通常来自 ASR 的句级或词级输出）。
输出：合并后的语义块列表（`TimedText`）。
"""
from __future__ import annotations

from typing import List, Sequence

from ..segment import TimedText

# 句子结束标点（停顿·标点边界切分依据）
_SENTENCE_END = "。！？；…!?.;\n"


def _join(items: Sequence[TimedText]) -> str:
    return "".join(t.text for t in items)


def _ends_with_sentence_end(text: str) -> bool:
    stripped = text.rstrip()
    return bool(stripped) and stripped[-1] in _SENTENCE_END


def chunk_fixed(items: Sequence[TimedText], window_sec: float = 15.0) -> List[TimedText]:
    """固定窗切分：按固定时长窗口累计文本，满 window_sec 即切一刀。"""
    chunks: List[TimedText] = []
    buf: List[TimedText] = []
    buf_start: float | None = None
    for t in items:
        if buf_start is None:
            buf_start = t.start
        buf.append(t)
        if t.end - buf_start >= window_sec:
            chunks.append(TimedText(buf_start, t.end, _join(buf)))
            buf, buf_start = [], None
    if buf:
        chunks.append(TimedText(buf_start, buf[-1].end, _join(buf)))
    return chunks


def chunk_sliding(
    items: Sequence[TimedText], window_sec: float = 15.0, step_sec: float = 7.5
) -> List[TimedText]:
    """滑动窗切分：时间轴上按 step_sec 滑动，取落入 [t, t+window_sec) 的文本（有重叠）。"""
    if not items:
        return []
    start, end = items[0].start, items[-1].end
    chunks: List[TimedText] = []
    t0 = start
    while t0 < end:
        seg = [x for x in items if x.end > t0 and x.start < t0 + window_sec]
        if seg:
            chunks.append(
                TimedText(max(t0, seg[0].start), min(t0 + window_sec, seg[-1].end), _join(seg))
            )
        t0 += step_sec
    return chunks


def chunk_pause_punctuation(
    items: Sequence[TimedText], min_sec: float = 10.0, max_sec: float = 20.0
) -> List[TimedText]:
    """停顿·标点边界切分（讲解型主策略）。

    优先在句子结束标点处切分；块时长尽量落在 [min_sec, max_sec] 之间：
    - 累计超过 max_sec 时强制切分（即使不在标点处）；
    - 累计超过 min_sec 且当前项以句末标点结尾时切分。
    """
    chunks: List[TimedText] = []
    buf: List[TimedText] = []
    buf_start: float | None = None
    for t in items:
        if buf_start is None:
            buf_start = t.start
        buf.append(t)
        span = t.end - buf_start
        if span >= max_sec:
            chunks.append(TimedText(buf_start, t.end, _join(buf)))
            buf, buf_start = [], None
        elif span >= min_sec and _ends_with_sentence_end(t.text):
            chunks.append(TimedText(buf_start, t.end, _join(buf)))
            buf, buf_start = [], None
    if buf:
        chunks.append(TimedText(buf_start, buf[-1].end, _join(buf)))
    return chunks


def chunk(
    items: Sequence[TimedText], strategy: str = "pause_punctuation", **kwargs
) -> List[TimedText]:
    """统一分块入口。strategy ∈ {fixed, sliding, pause_punctuation}。"""
    if strategy == "fixed":
        return chunk_fixed(items, **kwargs)
    if strategy == "sliding":
        return chunk_sliding(items, **kwargs)
    if strategy == "pause_punctuation":
        return chunk_pause_punctuation(items, **kwargs)
    raise ValueError(f"未知分块策略: {strategy!r}（可选 fixed / sliding / pause_punctuation）")
