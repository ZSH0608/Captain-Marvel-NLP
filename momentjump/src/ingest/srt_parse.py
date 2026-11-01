"""自写 SRT 字幕解析器（剧情型对白来源）。

SRT 块格式：:

    1
    00:00:01,000 --> 00:00:04,000
    字幕文本（可多行）

    （空行分隔块）

返回 `TimedText` 列表，供后续对话块合并 / 场景聚合使用。
"""
from __future__ import annotations

import re
from typing import List

from ..segment import TimedText

_TIME_RE = re.compile(r"(\d{1,2}):(\d{2}):(\d{2})[,.](\d{1,3})")


def _parse_time(s: str) -> float:
    m = _TIME_RE.search(s)
    if not m:
        raise ValueError(f"无法解析时间戳: {s!r}")
    h, mm, ss, ms = (int(g) for g in m.groups())
    return h * 3600 + mm * 60 + ss + ms / 1000.0


def parse_srt(text: str) -> List[TimedText]:
    """解析 SRT 文本，返回 [(start_sec, end_sec, text), ...]。"""
    normalized = text.strip().replace("\r\n", "\n").replace("\r", "\n")
    blocks = [b for b in normalized.split("\n\n") if b.strip()]
    out: List[TimedText] = []
    for block in blocks:
        lines = [l for l in block.split("\n") if l.strip()]
        if not lines:
            continue
        time_line = next((l for l in lines if "-->" in l), None)
        if time_line is None:
            continue
        start_s, end_s = time_line.split("-->")
        start = _parse_time(start_s.strip())
        end = _parse_time(end_s.strip())
        idx = lines.index(time_line)
        content = "\n".join(lines[idx + 1 :]).strip()
        if content:
            out.append(TimedText(start, end, content))
    return out


def parse_srt_file(path: str) -> List[TimedText]:
    """从文件读取并解析 SRT。"""
    with open(path, encoding="utf-8", errors="ignore") as f:
        return parse_srt(f.read())
