"""统一检索评测脚本：R@K / mIoU / 时间误差 + 基线对比。

输入：
  - 转写 JSON（句级时间戳，兼容 [{start,end,text}] 或 {segments:[...]}）
  - 检索 gold JSON（[query, video_id, gold_start, gold_end, ...]）

用法：:

    HF_HOME=/Volumes/T7/hf-cache python scripts/run_eval.py \
        --transcripts data/transcripts/match \
        --gold data/eval/match_dev.json \
        --retriever bm25        # bm25 | dense | hybrid

BM25-only 零重依赖；dense/hybrid 用 BGE（一次性编码，向量缓存复用）。
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
from src.retrieve.hybrid import reciprocal_rank_fusion
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


# ---------- 检索（复用缓存） ----------

def _bm25_rank(retriever: BM25Retriever, query: str, k: int) -> List[int]:
    return [i for i, _ in retriever.search(query, top_k=k)]


def _dense_rank(model, vecs, query: str, k: int) -> List[int]:
    from src.retrieve.dense import cosine_search

    qv = model.encode([query])
    return [i for i, _ in cosine_search(qv[0], vecs, top_k=k)]


# ---------- 评测 ----------

def evaluate(
    segments: Sequence[Segment],
    gold: Sequence[Dict],
    retriever: str,
    top_k: int,
    model_name: str = "BAAI/bge-base-zh-v1.5",
) -> Dict:
    by_video = group_by_video(segments)

    # 预构建 BM25（每个 video 一个）
    bm25 = {vid: BM25Retriever([s.text for s in segs]) for vid, segs in by_video.items()}

    # Dense/Hybrid：一次性编码，向量缓存复用
    dense_model = None
    vec_cache: Dict[str, object] = {}
    if retriever in ("dense", "hybrid"):
        from src.retrieve.dense import DenseRetriever

        dense_model = DenseRetriever(model_name=model_name)
        for vid, segs in by_video.items():
            vec_cache[vid] = dense_model.encode([s.text for s in segs])
            print(f"[编码] {vid}: {len(segs)} 个语义块")

    preds: List[List[Tuple[float, float]]] = []
    golds: List[Tuple[float, float]] = []
    for g in gold:
        vid = g["video_id"]
        segs = by_video.get(vid, [])
        spans: List[Tuple[float, float]] = []
        if segs:
            if retriever == "bm25":
                ids = _bm25_rank(bm25[vid], g["query"], top_k)
            elif retriever == "dense":
                ids = _dense_rank(dense_model, vec_cache[vid], g["query"], top_k)
            else:  # hybrid
                b_ids = _bm25_rank(bm25[vid], g["query"], max(top_k * 2, 10))
                d_ids = _dense_rank(dense_model, vec_cache[vid], g["query"], max(top_k * 2, 10))
                fused = reciprocal_rank_fusion([b_ids, d_ids])
                ids = [doc_id for doc_id, _ in fused[:top_k]]
            spans = [(segs[i].start_sec, segs[i].end_sec) for i in ids]
        preds.append(spans)
        golds.append((g["gold_start"], g["gold_end"]))

    delta = 10.0
    top1_preds = [p[0] for p in preds if p]
    top1_golds = [g for p, g in zip(preds, golds) if p]
    return {
        "n_queries": len(gold),
        "R@1": recall_at_k(preds, golds, k=1, delta=delta),
        "R@3": recall_at_k(preds, golds, k=3, delta=delta),
        "R@5": recall_at_k(preds, golds, k=5, delta=delta),
        "mean_iou": mean_iou(top1_preds, top1_golds) if top1_preds else float("nan"),
        "median_time_error": median_time_error(top1_preds, top1_golds) if top1_preds else float("nan"),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="运行检索评测")
    parser.add_argument("--transcripts", default="data/transcripts/match", help="转写目录或单文件")
    parser.add_argument("--gold", default="data/eval/match_dev.json")
    parser.add_argument("--retriever", default="bm25", choices=["bm25", "dense", "hybrid"])
    parser.add_argument("--top_k", type=int, default=5)
    parser.add_argument("--model", default="BAAI/bge-base-zh-v1.5", help="Dense/Hybrid 用的 embedding")
    args = parser.parse_args()

    gold = load_gold(args.gold)
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

    result = evaluate(segments, gold, args.retriever, args.top_k, model_name=args.model)
    print(f"\n===== {args.retriever} 评测结果（{os.path.basename(args.gold)}）=====")
    for k, v in result.items():
        if isinstance(v, float):
            print(f"{k}: {v:.4f}")
        else:
            print(f"{k}: {v}")


if __name__ == "__main__":
    main()
