"""统一 Segment 数据单元。

三类视频（讲解型 / 剧情型 / 赛事型）最终都落到同一种检索单元 `Segment`，
保证检索层与视频类别解耦——差异只隔离在 Ingest 的「信号来源」上（对应方案 §4）。
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Dict

DOMAINS = ("speech", "dialogue", "event")
SOURCE_TYPES = ("asr", "subtitle", "inferred_event", "caption")


@dataclass
class Segment:
    """一条可检索的视频片段。"""

    segment_id: str
    domain: str
    video_id: str
    title: str
    start_sec: float
    end_sec: float
    text: str
    source_type: str = "asr"
    meta: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.domain not in DOMAINS:
            raise ValueError(f"domain 必须是 {DOMAINS} 之一，得到 {self.domain!r}")
        if self.source_type not in SOURCE_TYPES:
            raise ValueError(f"source_type 必须是 {SOURCE_TYPES} 之一，得到 {self.source_type!r}")
        if self.end_sec < self.start_sec:
            raise ValueError(f"end_sec({self.end_sec}) 必须 >= start_sec({self.start_sec})")
        if not self.text or not self.text.strip():
            raise ValueError("text 不能为空")

    @property
    def duration(self) -> float:
        return self.end_sec - self.start_sec

    @property
    def center(self) -> float:
        return (self.start_sec + self.end_sec) / 2.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Segment":
        return cls(**d)


@dataclass
class TimedText:
    """带时间戳的文本片段（chunking / SRT 解析的输入输出单元）。"""

    start: float
    end: float
    text: str

    @property
    def duration(self) -> float:
        return self.end - self.start
