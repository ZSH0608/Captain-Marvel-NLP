"""LLM few-shot 事件识别（本地 ollama）。

用本地大模型对解说窗口做 few-shot 结构化事件抽取，替换/融合规则基线
（对应方案 §5.3 的「LLM few-shot 抽取」）。相比规则基线，few-shot 能
理解"这一分结束""得分方"等语义，显著降低误报。

依赖：本地 ollama（`ollama run qwen2.5:3b` 等模型）。
"""
from __future__ import annotations

import json
from typing import Dict, List, Optional

import requests

OLLAMA_URL = "http://localhost:11434/api/generate"

SYSTEM_PROMPT = (
    "你是羽毛球比赛解说事件识别器。给定带时间戳的解说文本，识别其中的比分与事件。\n"
    "事件类型（严格从以下选）：\n"
    "- point_start: 一分开始（发球）\n"
    "- point_end: 一分结束（某方得分，如杀球得分、对手失误送分、降速）\n"
    "- score_change: 解说报出具体比分\n"
    "- other: 其他事件（挑战、界内/界外判定、回放点评等）\n"
    "输出 JSON 数组，每个事件一个对象，字段：event_type, start_sec, end_sec, "
    "winner_side(A/B/null), score_after, evidence_text。\n"
    "注意：score_after 只在解说明确报出比分（如\"4比1\"）时才填\"a:b\"格式，否则一律 null；"
    "winner_side 只在该句明确指向某方得分/领先时才填 A 或 B，否则 null。\n"
    "只输出 JSON 数组本身，不要解释、不要 markdown 代码块。"
)

FEWSHOT_EXAMPLES = (
    "示例1：\n输入：[{\"start\":53.1,\"end\":53.82,\"text\":\"黄雅琼发球\"}]\n"
    "输出：[{\"event_type\":\"point_start\",\"start_sec\":53.1,\"end_sec\":53.82,"
    "\"winner_side\":null,\"score_after\":null,\"evidence_text\":\"黄雅琼发球\"}]\n"
    "示例2：\n输入：[{\"start\":218.71,\"end\":220.23,\"text\":\"开局取得了4比1的领先\"}]\n"
    "输出：[{\"event_type\":\"score_change\",\"start_sec\":218.71,\"end_sec\":220.23,"
    "\"winner_side\":\"A\",\"score_after\":\"4:1\",\"evidence_text\":\"开局取得了4比1的领先\"}]\n"
    "示例3：\n输入：[{\"start\":230.0,\"end\":232.5,\"text\":\"郑思维杀球得分了\"}]\n"
    "输出：[{\"event_type\":\"point_end\",\"start_sec\":230.0,\"end_sec\":232.5,"
    "\"winner_side\":\"A\",\"score_after\":null,\"evidence_text\":\"郑思维杀球得分了\"}]"
)


def _window_to_input(window: List[Dict]) -> str:
    """把窗口（list of {start,end,text}）转成 prompt 输入。"""
    return json.dumps(
        [{"start": w["start"], "end": w["end"], "text": w["text"]} for w in window],
        ensure_ascii=False,
    )


def llm_spot_window(
    window: List[Dict],
    side_a: str,
    side_b: str,
    model: str = "qwen2.5:3b",
    timeout: int = 180,
) -> List[Dict]:
    """对单个窗口做 few-shot 事件识别，返回解析后的事件列表。"""
    prompt = (
        f"{SYSTEM_PROMPT}\n\n{FEWSHOT_EXAMPLES}\n\n"
        f"A方（{side_a}）；B方（{side_b}）。\n"
        f"输入：{_window_to_input(window)}\n输出："
    )
    try:
        resp = requests.post(
            OLLAMA_URL,
            json={"model": model, "prompt": prompt, "stream": False},
            timeout=timeout,
        )
        resp.raise_for_status()
        raw = resp.json()["response"]
    except Exception as e:  # noqa: BLE001
        print(f"[LLM 调用失败] {e}")
        return []
    return _parse_events(raw)


def _parse_events(raw: str) -> List[Dict]:
    """从 LLM 输出中提取事件 JSON 数组（容错：去掉 markdown 代码块）。"""
    raw = raw.strip()
    # 去掉 ```json ... ``` 包裹
    if raw.startswith("```"):
        raw = raw.strip("`")
        if raw.startswith("json"):
            raw = raw[4:]
    # 定位 JSON 数组
    start = raw.find("[")
    end = raw.rfind("]")
    if start == -1 or end == -1 or end <= start:
        return []
    try:
        data = json.loads(raw[start : end + 1])
    except json.JSONDecodeError:
        return []
    events = []
    for d in data:
        if not isinstance(d, dict) or "event_type" not in d:
            continue
        events.append(
            {
                "event_type": str(d.get("event_type", "other")),
                "start_sec": float(d.get("start_sec", 0.0)),
                "end_sec": float(d.get("end_sec", 0.0)),
                "winner_side": d.get("winner_side") or None,
                "score_after": d.get("score_after") or None,
                "evidence_text": str(d.get("evidence_text", "")),
            }
        )
    return events


def chunk_windows(items: List[Dict], window_size: int = 15) -> List[List[Dict]]:
    """把解说句列表按 window_size 句切成窗口。"""
    return [items[i : i + window_size] for i in range(0, len(items), window_size)]


def llm_spot_transcript(
    items: List[Dict],
    side_a: str,
    side_b: str,
    model: str = "qwen2.5:3b",
    window_size: int = 15,
) -> List[Dict]:
    """对整段转写做 few-shot 事件识别（分窗口，逐个调用 LLM）。"""
    events: List[Dict] = []
    windows = chunk_windows(items, window_size)
    for wi, w in enumerate(windows):
        evs = llm_spot_window(w, side_a, side_b, model=model)
        events.extend(evs)
        print(f"[LLM] 窗口 {wi + 1}/{len(windows)}：识别 {len(evs)} 个事件")
    return events
