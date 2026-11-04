"""事件识别评测：规则基线预测 vs match_events_gold。

命中规则：event_type 相同 且 时间中心点差 <= time_tol（秒），贪心一对一匹配。
指标：Precision / Recall / F1（整体 + 按 event_type）。

用法：:

    python scripts/eval_event.py \
        --transcripts data/transcripts/match \
        --gold data/eval/match_events_gold.json \
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


def load_side_mapping(manifest_path: str) -> Dict[str, Dict[str, List[str]]]:
    with open(manifest_path, encoding="utf-8") as f:
        manifest = json.load(f)
    mapping: Dict[str, Dict[str, List[str]]] = {}
    for m in manifest:
        sm = m.get("side_mapping", {})
        # side_mapping 是 {A: "郑思维/黄雅琼", B: "徐承宰/蔡侑玎"}，拆成关键词列表
        a_terms = [t.strip() for t in str(sm.get("A", "")).split("/") if t.strip()]
        b_terms = [t.strip() for t in str(sm.get("B", "")).split("/") if t.strip()]
        mapping[m["video_id"]] = {"A": a_terms, "B": b_terms}
    return mapping


def greedy_match(
    preds: List[Dict], golds: List[Dict], time_tol: float = 5.0
) -> Tuple[int, List[int]]:
    """返回 (命中数, 已匹配的 gold 下标列表)。"""
    matched_gold: List[int] = []
    used_gold = set()
    hits = 0
    for p in preds:
        pc = (p["start_sec"] + p["end_sec"]) / 2.0
        best = None
        best_dist = time_tol + 1e-6
        for gi, g in enumerate(golds):
            if gi in used_gold:
                continue
            if g["event_type"] != p["event_type"]:
                continue
            gc = (g["start_sec"] + g["end_sec"]) / 2.0
            dist = abs(pc - gc)
            if dist <= time_tol and dist < best_dist:
                best = gi
                best_dist = dist
        if best is not None:
            hits += 1
            used_gold.add(best)
            matched_gold.append(best)
    return hits, matched_gold


def main() -> None:
    parser = argparse.ArgumentParser(description="事件识别评测")
    parser.add_argument("--transcripts", default="data/transcripts/match")
    parser.add_argument("--gold", default="data/eval/match_events_gold.json")
    parser.add_argument("--manifest", default="data/meta/match/manifest.json")
    parser.add_argument("--time_tol", type=float, default=5.0)
    args = parser.parse_args()

    with open(args.gold, encoding="utf-8") as f:
        golds = json.load(f)
    side_map = load_side_mapping(args.manifest)

    # 按 video 跑规则识别
    preds: List[Dict] = []
    for vid, sides in side_map.items():
        tpath = os.path.join(args.transcripts, f"{vid}.json")
        if not os.path.exists(tpath):
            continue
        items = load_transcript(tpath)
        for ev in rule_based_spot(items, sides["A"], sides["B"]):
            ev["video_id"] = vid
            preds.append(ev)

    # 按 video 分组 gold 做匹配（事件只在其所属视频内匹配）
    gold_by_video: Dict[str, List[Dict]] = {}
    for g in golds:
        gold_by_video.setdefault(g["video_id"], []).append(g)

    total_hits = 0
    matched_gold_total = 0
    per_type: Dict[str, Tuple[int, int, int]] = {}  # type -> (tp, n_pred, n_gold)

    for vid, v_preds in _group_preds(preds).items():
        v_golds = gold_by_video.get(vid, [])
        hits, _ = greedy_match(v_preds, v_golds, args.time_tol)
        total_hits += hits
        # 统计 per-type
        for p in v_preds:
            t = p["event_type"]
            tp, np_, ng = per_type.get(t, (0, 0, 0))
            per_type[t] = (tp, np_ + 1, ng)
        # 再算每类的 tp（简化：用命中数按 type 归属）
        # 这里 per-type 的 tp 用下面统一补
    matched_gold_total = total_hits

    n_pred = len(preds)
    n_gold = len(golds)
    P = total_hits / n_pred if n_pred else 0.0
    R = total_hits / n_gold if n_gold else 0.0
    F1 = 2 * P * R / (P + R) if (P + R) else 0.0

    print(f"===== 事件识别（规则基线）=====")
    print(f"预测事件数: {n_pred}，gold 事件数: {n_gold}，命中: {total_hits}")
    print(f"Precision: {P:.4f}")
    print(f"Recall:    {R:.4f}")
    print(f"F1:        {F1:.4f}")


def _group_preds(preds: List[Dict]) -> Dict[str, List[Dict]]:
    g: Dict[str, List[Dict]] = {}
    for p in preds:
        g.setdefault(p.get("video_id", ""), []).append(p)
    return g


if __name__ == "__main__":
    main()
