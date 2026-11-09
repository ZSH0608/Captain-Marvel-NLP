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
# 一分结束 / 得分类词（含「失误得分」：gold point_end 主体是失误/出界）
_POINT_END_WORDS = ["得分", "拿分", "得一分", "赢下这一分", "收吊", "杀球", "好球",
                    "得分了", "扳回", "追平", "拿下", "结束这一分", "降速", "这一分",
                    "失误", "出界", "滚网", "拍框", "没打准", "失分"]
# 其他事件（挑战鹰眼 / 技术动作 / 球拍碰撞）
_OTHER_WORDS = ["挑战", "封网", "球拍撞", "球拍打", "界内球", "界外球"]
# 比分正则：数字[:：比]数字，或"几比几"
_SCORE_RE = re.compile(r"(\d{1,2})\s*[:：比]\s*(\d{1,2})")
_LEAD_RE = re.compile(r"(\d{1,2})\s*比\s*(\d{1,2})")

# 中文数字比分（Whisper 常把"11比7"转成"十一比七"）：一~九十九
_CN_DIGIT = {"零": 0, "一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6,
             "七": 7, "八": 8, "九": 9}
_CN_NUM = "[零一二三四五六七八九十]{1,3}"
_CN_SCORE_RE = re.compile(rf"({_CN_NUM})\s*比\s*({_CN_NUM})")
# 平局：数字或中文数字 + "平"（如"14平""十九平"）
_TIE_RE = re.compile(rf"(\d{{1,2}}|{_CN_NUM})\s*平")


def _cn_to_int(s: str) -> int:
    """中文数字 → 整数（支持 零~九十九）。"""
    if s.isdigit():
        return int(s)
    if s == "十":
        return 10
    if "十" in s:
        tens, _, ones = s.partition("十")
        t = _CN_DIGIT.get(tens, 1) if tens else 1
        o = _CN_DIGIT.get(ones, 0) if ones else 0
        return t * 10 + o
    return _CN_DIGIT.get(s, 0)


def extract_scores(text: str) -> List[Tuple[int, int]]:
    """从解说文本提取比分，返回 [(a, b), ...]（含阿拉伯/中文数字 + 平局）。"""
    scores: List[Tuple[int, int]] = []
    for m in _SCORE_RE.finditer(text):
        scores.append((int(m.group(1)), int(m.group(2))))
    for m in _CN_SCORE_RE.finditer(text):
        scores.append((_cn_to_int(m.group(1)), _cn_to_int(m.group(2))))
    for m in _TIE_RE.finditer(text):
        n = _cn_to_int(m.group(1))
        scores.append((n, n))  # 平局 → n:n
    return scores


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
        # 1) 比分变化（阿拉伯/中文数字 + 平局，以裁判/解说报分为主）
        scores = extract_scores(text)
        if scores:
            a, b = scores[0]
            events.append({
                "event_type": "score_change",
                "start_sec": t.start,
                "end_sec": t.end,
                "winner_side": infer_winner_side(text, side_a_terms or [], side_b_terms or []),
                "score_after": f"{a}:{b}",
                "evidence_text": text,
            })
            continue
        # 2) 得分词 → point_end（优先于发球，因「发球失误」是得分不是发球）
        if any(w in text for w in _POINT_END_WORDS):
            events.append({
                "event_type": "point_end",
                "start_sec": t.start,
                "end_sec": t.end,
                "winner_side": infer_winner_side(text, side_a_terms or [], side_b_terms or []),
                "score_after": None,
                "evidence_text": text,
            })
            continue
        # 3) 发球 → point_start
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
        # 4) 其他事件（挑战鹰眼 / 封网 / 球拍碰撞）
        if any(w in text for w in _OTHER_WORDS):
            events.append({
                "event_type": "other",
                "start_sec": t.start,
                "end_sec": t.end,
                "winner_side": infer_winner_side(text, side_a_terms or [], side_b_terms or []),
                "score_after": None,
                "evidence_text": text,
            })
    return events
