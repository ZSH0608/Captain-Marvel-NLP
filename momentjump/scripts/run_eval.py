"""统一检索评测脚本：R@K / mIoU / 时间误差 + 基线对比。

输入：
  - 转写 JSON（句级时间戳，兼容 [{start,end,text}] 或 {segments:[...]}）
  - 检索 gold JSON（[query, video_id, gold_start, gold_end, ...]）

用法：:

    python scripts/run_eval.py \
        --transcripts data/transcripts/match \
        --gold data/eval/match_dev.json \
        --retriever bm25        # bm25 | dense | hybrid（dense/hybrid 需先下载 BGE 权重）

BM25-only 零重依赖，拿到转写即可跑出第一条基线。
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Dict, List, Sequence, Tuple

# 让 `python scripts/run_eval.py` 从任意目录运行都能 import src
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.eval.metrics import mean_iou, median_time_error, recall_at_k
from src.ingest.chunking import chunk_pause_punctuation
from src.retrieve.bm25 import BM25Retriever
from src.segment import Segment, TimedText


# ---------- 加载 ----------

def load_transcript(path: str) -> List[TimedText]:
    """加载转写 JSON，返回句级 TimedText 列表（兼容多种常见格式）。"""
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict) and "segments" in data:
        data = data["segments"]
    items: List[TimedText] = []
    for d in data:
        start = d.get("start", d.get("start_sec"))
        end = d.get("end", d.get("end_sec"))
        text = d.get("text", "")
        if start is None or end is None or not str(text).strip():
            continue
        items.append(TimedText(float(start), float(end), str(text).strip()))
    return items


def load_gold(path: str) -> List[Dict]:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


# ---------- 建索引 ----------

def build_segments(
    items: Sequence[TimedText],
    video_id: str,
    title: str,
    domain: str = "event",
    min_sec: float = 8.0,
    max_sec: float = 18.0,
) -> List[Segment]:
    """按停顿·标点边界切分并组装成 Segment。"""
    chunks = chunk_pause_punctuation(items, min_sec=min_sec, max_sec=max_sec)
    return [
        Segment(
            segment_id=f"{video_id}_{i:04d}",
            domain=domain,
            video_id=video_id,
            title=title,
            start_sec=c.start,
            end_sec=c.end,
            text=c.text,
            source_type="asr",
        )
        for i, c in enumerate(chunks)
    ]


def group_by_video(segments: Sequence[Segment]) -> Dict[str, List[Segment]]:
    g: Dict[str, List[Segment]] = {}
    for s in segments:
        g.setdefault(s.video_id, []).append(s)
    return g


# ---------- 检索 ----------

def run_bm25(video_segs: Sequence[Segment], query: str, top_k: int) -> List[Tuple[float, float]]:
    retriever = BM25Retriever([s.text for s in video_segs])
    hits = retriever.search(query, top_k=top_k)
    return [(video_segs[i].start_sec, video_segs[i].end_sec) for i, _ in hits]


def run_dense(video_segs: Sequence[Segment], query: str, top_k: int) -> List[Tuple[float, float]]:
    from src.retrieve.dense import DenseRetriever

    dr = DenseRetriever()
    vecs = dr.encode([s.text for s in video_segs])
    qv = dr.encode([query])
    hits = dr.search(qv[0], top_k=top_k)
    return [(video_segs[i].start_sec, video_segs[i].end_sec) for i, _ in hits]


def run_hybrid(video_segs: Sequence[Segment], query: str, top_k: int) -> List[Tuple[float, float]]:
    from src.retrieve.dense import DenseRetriever
    from src.retrieve.hybrid import reciprocal_rank_fusion

    bm25 = BM25Retriever([s.text for s in video_segs])
    bm25_ranked = [i for i, _ in bm25.search(query, top_k=max(top_k * 2, 10))]

    dr = DenseRetriever()
    vecs = dr.encode([s.text for s in video_segs])
    qv = dr.encode([query])
    dense_ranked = [i for i, _ in dr.search(qv[0], top_k=max(top_k * 2, 10))]

    fused = reciprocal_rank_fusion([bm25_ranked, dense_ranked])
    top_ids = [doc_id for doc_id, _ in fused[:top_k]]
    return [(video_segs[i].start_sec, video_segs[i].end_sec) for i in top_ids]


# ---------- 评测 ----------

def evaluate(segments: Sequence[Segment], gold: Sequence[Dict], retriever: str, top_k: int) -> Dict:
    by_video = group_by_video(segments)
    retriever_fn = {"bm25": run_bm25, "dense": run_dense, "hybrid": run_hybrid}[retriever]

    preds: List[List[Tuple[float, float]]] = []
    golds: List[Tuple[float, float]] = []
    for g in gold:
        segs = by_video.get(g["video_id"], [])
        if not segs:
            preds.append([])
        else:
            preds.append(retriever_fn(segs, g["query"], top_k))
        golds.append((g["gold_start"], g["gold_end"]))

    delta = 10.0
    top1_preds = [p[0] for p in preds if p]
    top1_golds = [g for p, g in zip(preds, golds) if p]
    return {
        "n_queries": len(gold),
        f"R@1": recall_at_k(preds, golds, k=1, delta=delta),
        f"R@3": recall_at_k(preds, golds, k=3, delta=delta),
        f"R@5": recall_at_k(preds, golds, k=5, delta=delta),
        "median_time_error": median_time_error(top1_preds, top1_golds) if top1_preds else float("nan"),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="运行检索评测")
    parser.add_argument("--transcripts", default="data/transcripts/match", help="转写目录或单文件")
    parser.add_argument("--gold", default="data/eval/match_dev.json")
    parser.add_argument("--retriever", default="bm25", choices=["bm25", "dense", "hybrid"])
    parser.add_argument("--top_k", type=int, default=5)
    args = parser.parse_args()

    gold = load_gold(args.gold)
    # 按 gold 引用的 video 加载转写
    needed_videos = sorted({g["video_id"] for g in gold})
    segments: List[Segment] = []
    for vid in needed_videos:
        tpath = os.path.join(args.transcripts, f"{vid}.json")
        if not os.path.exists(tpath):
            print(f"[警告] 缺转写文件：{tpath}，该视频的 query 将被跳过")
            continue
        items = load_transcript(tpath)
        segs = build_segments(items, video_id=vid, title=vid)
        segments.extend(segs)
        print(f"[加载] {vid}: {len(items)} 句转写 → {len(segs)} 个语义块")

    if not segments:
        print("[错误] 没有任何转写可评测，请确认 --transcripts 路径正确")
        return

    result = evaluate(segments, gold, args.retriever, args.top_k)
    print(f"\n===== {args.retriever} 评测结果（{os.path.basename(args.gold)}）=====")
    for k, v in result.items():
        if isinstance(v, float):
            print(f"{k}: {v:.4f}")
        else:
            print(f"{k}: {v}")


if __name__ == "__main__":
    main()
