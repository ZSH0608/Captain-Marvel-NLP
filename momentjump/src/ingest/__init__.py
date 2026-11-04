"""Ingest 层：视频/字幕/解说 → 分块 → 嵌入 → 建索引。"""

from .chunking import chunk, chunk_fixed, chunk_pause_punctuation, chunk_sliding
from .event_spotting import rule_based_spot
from .srt_parse import parse_srt, parse_srt_file

__all__ = [
    "chunk",
    "chunk_fixed",
    "chunk_sliding",
    "chunk_pause_punctuation",
    "rule_based_spot",
    "parse_srt",
    "parse_srt_file",
]
