"""事件识别评测：规则基线 / LLM few-shot 预测 vs match_events_gold。

命中规则：event_type 相同 且 时间中心点差 <= time_tol（秒），贪心一对一匹配。
指标：Precision / Recall / F1（整体）。

用法：:

    python scripts/eval_event.py --method rule \
        --transcripts data/transcripts/match --gold data/eval/match_events_gold.json \
        --manifest data/meta/match/manifest.json

    python scripts/eval_event.py --method llm --model qwen2.5:3b \
        --transcripts data/transcripts/match --gold data/eval/match_events_gold.json \
        --manifest data/meta/match/manifest.json
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Dict, List, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.ingest.event_spotting import rule_based_spot
from src.segment import TimedText


def load_transcript(path: str) -> List[TimedText]:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict) and "segments" in data:
        data = data["segments"]
    return [
        TimedText(float(d["start"]), float(d["end"]), str(d.get("text", "")).strip())
        for d in data
        if str(d.get("text", "")).strip()
    ]


def load_side_mapping(manifest_path: str) -> Dict[str, Tuple[str, str]]:
    """返回 {video_id: (side_a_str, side_b_str)}。"""
    with open(manifest_path, encoding="utf-8") as f:
        manifest = json.load(f)
    mapping: Dict[str, Tuple[str, str]] = {}
    for m in manifest:
        sm = m.get("side_mapping", {})
        mapping[m["video_id"]] = (str(sm.get("A", "")), str(sm.get("B", "")))
    return mapping


def greedy_match(preds: List[Dict], golds: List[Dict], time_tol: float = 5.0) -> int:
    """贪心一对一匹配，返回命中数。"""
    used_gold = set()
    hits = 0
    for p in preds:
        pc = (p["start_sec"] + p["end_sec"]) / 2.0
        best, best_dist = None, time_tol + 1e-6
        for gi, g in enumerate(golds):
            if gi in used_gold or g["event_type"] != p["event_type"]:
                continue
            gc = (g["start_sec"] + g["end_sec"]) / 2.0
            dist = abs(pc - gc)
            if dist <= time_tol and dist < best_dist:
                best, best_dist = gi, dist
        if best is not None:
            hits += 1
            used_gold.add(best)
    return hits


def run_rule(items_by_video: Dict[str, List[TimedText]], side_map) -> List[Dict]:
    preds: List[Dict] = []
    for vid, items in items_by_video.items():
        a, b = side_map[vid]
        a_terms = [t.strip() for t in a.split("/") if t.strip()]
        b_terms = [t.strip() for t in b.split("/") if t.strip()]
        for ev in rule_based_spot(items, a_terms, b_terms):
            ev["video_id"] = vid
            preds.append(ev)
    return preds


def run_llm(items_by_video: Dict[str, List[TimedText]], side_map, model: str, cache_path: str = "data/reports/llm_pred_events.json") -> List[Dict]:
    """LLM few-shot 识别，带结果缓存（避免重复调用 LLM）。"""
    if os.path.exists(cache_path):
        with open(cache_path, encoding="utf-8") as f:
            return json.load(f)

    from src.ingest.event_spotting_llm import llm_spot_transcript

    preds: List[Dict] = []
    for vid, items in items_by_video.items():
        a, b = side_map[vid]
        windows_input = [
            {"start": t.start, "end": t.end, "text": t.text} for t in items
        ]
        evs = llm_spot_transcript(windows_input, a, b, model=model)
        for ev in evs:
            ev["video_id"] = vid
        preds.extend(evs)

    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(preds, f, ensure_ascii=False, indent=2)
    return preds


def run_fusion(
    items_by_video: Dict[str, List[TimedText]],
    side_map,
    model: str,
    cache_path: str = "data/reports/fusion_pred_events.json",
) -> List[Dict]:
    """规则召回 + LLM 精排（融合），带结果缓存。"""
    if os.path.exists(cache_path):
        with open(cache_path, encoding="utf-8") as f:
            return json.load(f)

    from src.ingest.event_spotting_llm import llm_refine_rule_events

    preds: List[Dict] = []
    for vid, items in items_by_video.items():
        a, b = side_map[vid]
        a_terms = [t.strip() for t in a.split("/") if t.strip()]
        b_terms = [t.strip() for t in b.split("/") if t.strip()]
        rule_events = rule_based_spot(items, a_terms, b_terms)
        refined = llm_refine_rule_events(rule_events, a, b, model=model)
        for ev in refined:
            ev["video_id"] = vid
        preds.extend(refined)

    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(preds, f, ensure_ascii=False, indent=2)
    return preds


def main() -> None:
    parser = argparse.ArgumentParser(description="事件识别评测")
    parser.add_argument("--method", default="rule", choices=["rule", "llm", "fusion"])
    parser.add_argument("--model", default="qwen2.5:3b", help="llm 模式用的 ollama 模型")
    parser.add_argument("--transcripts", default="data/transcripts/match")
    parser.add_argument("--gold", default="data/eval/match_events_gold.json")
    parser.add_argument("--manifest", default="data/meta/match/manifest.json")
    parser.add_argument("--time_tol", type=float, default=5.0)
    args = parser.parse_args()

    with open(args.gold, encoding="utf-8") as f:
        golds = json.load(f)
    side_map = load_side_mapping(args.manifest)

    items_by_video: Dict[str, List[TimedText]] = {}
    for vid in side_map:
        tpath = os.path.join(args.transcripts, f"{vid}.json")
        if os.path.exists(tpath):
            items_by_video[vid] = load_transcript(tpath)

    if args.method == "llm":
        preds = run_llm(items_by_video, side_map, args.model)
    elif args.method == "fusion":
        preds = run_fusion(items_by_video, side_map, args.model)
    else:
        preds = run_rule(items_by_video, side_map)

    # 按 video 分组 gold
    gold_by_video: Dict[str, List[Dict]] = {}
    for g in golds:
        gold_by_video.setdefault(g["video_id"], []).append(g)

    pred_by_video: Dict[str, List[Dict]] = {}
    for p in preds:
        pred_by_video.setdefault(p.get("video_id", ""), []).append(p)

    total_hits = 0
    for vid, v_preds in pred_by_video.items():
        total_hits += greedy_match(v_preds, gold_by_video.get(vid, []), args.time_tol)

    n_pred, n_gold = len(preds), len(golds)
    P = total_hits / n_pred if n_pred else 0.0
    R = total_hits / n_gold if n_gold else 0.0
    F1 = 2 * P * R / (P + R) if (P + R) else 0.0

    print(f"===== 事件识别（{args.method}）=====")
    print(f"预测事件数: {n_pred}，gold 事件数: {n_gold}，命中: {total_hits}")
    print(f"Precision: {P:.4f}")
    print(f"Recall:    {R:.4f}")
    print(f"F1:        {F1:.4f}")


if __name__ == "__main__":
    main()
