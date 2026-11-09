"""剧情型（剧集）检索评测：场景级（brief 情节摘要）检索。

剧集型的查询是「情节描述」，与零散对白词级/语义都难对齐；场景 brief 是
人工情节摘要，与 query 同属情节语义，是剧集型检索的核心文档来源。

用法：:

    HF_HOME=/Volumes/T7/hf-cache python scripts/eval_drama.py \
        --gold data/eval/drama_dev.json --retriever dense   # bm25 | dense
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import sys
from typing import Dict, List, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.retrieve.bm25 import BM25Retriever


def load_scenes(scenes_dir: str = "data/meta/drama/scenes") -> List[Tuple[str, str, float, float, str]]:
    """返回 [(video_id, scene_id, start_sec, end_sec, brief), ...]。"""
    docs = []
    for path in sorted(glob.glob(os.path.join(scenes_dir, "*.scenes.json"))):
        vid = os.path.basename(path).replace(".scenes.json", "")
        for s in json.load(open(path, encoding="utf-8")):
            docs.append((vid, s["scene_id"], s["start_sec"], s["end_sec"], s["brief"]))
    return docs


def _cover(doc: Tuple[str, str, float, float, str], gold: Dict) -> bool:
    """场景是否覆盖 gold 时间窗（同 video 且时间窗包含 gold）。"""
    vid, _, s0, s1, _ = doc
    return vid == gold["video_id"] and s0 <= gold["gold_start"] and s1 >= gold["gold_end"]


def evaluate_scene(
    docs: List[Tuple[str, str, float, float, str]],
    gold: List[Dict],
    retriever: str = "dense",
    top_k: int = 1,
    model_name: str = "BAAI/bge-base-zh-v1.5",
) -> Dict:
    briefs = [d[4] for d in docs]
    bm25 = BM25Retriever(briefs)

    dense_model = None
    vecs = None
    if retriever == "dense":
        import numpy as np
        from src.retrieve.dense import DenseRetriever, _resolve_local_snapshot

        dense_model = DenseRetriever(model_name=model_name)
        vecs = dense_model.encode(briefs)
        print(f"[编码] {len(briefs)} 个场景 brief")

    hits_at_k = {k: 0 for k in range(1, top_k + 1)}
    for g in gold:
        if retriever == "bm25":
            ranked = bm25.search(g["query"], top_k=top_k)
        else:
            import numpy as np

            qv = dense_model.encode([g["query"]])
            ranked = [(i, float(s)) for i, s in _cosine_rank(qv[0], vecs, top_k)]
        for rank, (idx, _) in enumerate(ranked, start=1):
            if _cover(docs[idx], g):
                for k in range(rank, top_k + 1):
                    hits_at_k[k] += 1
                break

    n = len(gold)
    return {f"R@{k}": hits_at_k[k] / n for k in range(1, top_k + 1)} | {"n_queries": n}


def _cosine_rank(qv, D, top_k):
    import numpy as np

    q = np.asarray(qv, dtype="float32")
    D = np.asarray(D, dtype="float32")
    q = q / (np.linalg.norm(q) + 1e-9)
    D = D / (np.linalg.norm(D, axis=1, keepdims=True) + 1e-9)
    sims = D @ q
    order = np.argsort(-sims)[:top_k]
    return [(int(i), float(sims[i])) for i in order]


def main() -> None:
    parser = argparse.ArgumentParser(description="剧情型场景级检索评测")
    parser.add_argument("--gold", default="data/eval/drama_dev.json")
    parser.add_argument("--retriever", default="dense", choices=["bm25", "dense"])
    parser.add_argument("--top_k", type=int, default=3)
    args = parser.parse_args()

    docs = load_scenes()
    gold = json.load(open(args.gold, encoding="utf-8"))
    result = evaluate_scene(docs, gold, retriever=args.retriever, top_k=args.top_k)
    print(f"\n===== 剧集型场景级检索（{args.retriever}，{os.path.basename(args.gold)}）=====")
    for k, v in result.items():
        if isinstance(v, float):
            print(f"{k}: {v:.4f}")
        else:
            print(f"{k}: {v}")


if __name__ == "__main__":
    main()
