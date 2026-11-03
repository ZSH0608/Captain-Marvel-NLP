"""赛事解说事件识别（Commentary-based Event Spotting）——规则基线 + 接口。

从解说文本中自动推断事件（point_start / point_end / score_change / other），
不依赖人工事件标注（对应方案 §5.3）。规则版零依赖可立即跑；LLM few-shot 版见
README 待办清单（参考 arXiv:2506.17144）。

输入：解说句级转写 `List[TimedText]`。
输出：事件列表 `List[dict]`，字段与 `match_events_gold.json` 对齐。
"""
from __future__ import annotations

import re
from typing import Dict, List, Optional

from ..segment import TimedText

# 一分开始：发球类词
_POINT_START_WORDS = ["发球", "发球权", "开球", "换发球"]
# 一分结束 / 得分类词
_POINT_END_WORDS = ["得分", "拿分", "得一分", "赢下这一分", "收吊", "杀球", "好球",
                    "得分了", "扳回", "追平", "拿下", "结束这一分", "降速", "这一分"]
# 比分正则：数字[:：比]数字，或"几比几"
_SCORE_RE = re.compile(r"(\d{1,2})\s*[:：比]\s*(\d{1,2})")
_LEAD_RE = re.compile(r"(\d{1,2})\s*比\s*(\d{1,2})")


def infer_winner_side(
    text: str, side_a_terms: List[str], side_b_terms: List[str]
) -> Optional[str]:
    """按 A/B 方关键词（选手名/组合名）判断得分方。"""
    has_a = any(t in text for t in side_a_terms) if side_a_terms else False
    has_b = any(t in text for t in side_b_terms) if side_b_terms else False
    if has_a and not has_b:
        return "A"
    if has_b and not has_a:
        return "B"
    return None


def rule_based_spot(
    items: List[TimedText],
    side_a_terms: Optional[List[str]] = None,
    side_b_terms: Optional[List[str]] = None,
) -> List[Dict]:
    """规则基线：按关键词 + 比分正则从解说中识别事件。"""
    events: List[Dict] = []
    for i, t in enumerate(items):
        text = t.text
        # 比分变化
        m = _SCORE_RE.search(text) or _LEAD_RE.search(text)
        if m:
            a, b = int(m.group(1)), int(m.group(2))
            events.append({
                "event_type": "score_change",
                "start_sec": t.start,
                "end_sec": t.end,
                "winner_side": infer_winner_side(text, side_a_terms or [], side_b_terms or []),
                "score_after": f"{a}:{b}",
                "evidence_text": text,
            })
            continue
        # 发球 → 一分开始
        if any(w in text for w in _POINT_START_WORDS):
            events.append({
                "event_type": "point_start",
                "start_sec": t.start,
                "end_sec": t.end,
                "winner_side": None,
                "score_after": None,
                "evidence_text": text,
            })
            continue
        # 得分词 → 一分结束
        if any(w in text for w in _POINT_END_WORDS):
            events.append({
                "event_type": "point_end",
                "start_sec": t.start,
                "end_sec": t.end,
                "winner_side": infer_winner_side(text, side_a_terms or [], side_b_terms or []),
                "score_after": None,
                "evidence_text": text,
            })
    return events
