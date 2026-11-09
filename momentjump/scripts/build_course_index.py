"""讲解型（课程）索引构建脚本。

讲解型转写由成员交付（已 ASR + 分块），本脚本负责：读成员转写 → 统一字段格式
→ 输出标准转写 JSON（供 run_eval.py 检索评测）。

成员交付的 .segments.json 有两种字段（成员 1 用 start_sec/end_sec，成员 2 用
start/end），这里统一为 [{start, end, text}]。

用法：:

    python scripts/build_course_index.py \
        --src "/Volumes/T7/speech,/Volumes/T7/speech2/transcripts" \
        --out data/transcripts/speech
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import sys
from typing import Dict, List

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _s_start(s: Dict) -> float:
    return s.get("start_sec", s.get("start"))


def _s_end(s: Dict) -> float:
    return s.get("end_sec", s.get("end"))


def main() -> None:
    parser = argparse.ArgumentParser(description="构建讲解型课程索引（统一成员转写格式）")
    parser.add_argument("--src", default="/Volumes/T7/speech,/Volumes/T7/speech2/transcripts",
                        help="成员转写目录，逗号分隔")
    parser.add_argument("--out", default="data/transcripts/speech")
    args = parser.parse_args()

    src_dirs = [d.strip() for d in args.src.split(",") if d.strip()]
    os.makedirs(args.out, exist_ok=True)

    # 收集每个 video_id 的 .segments.json（优先）或 .json（回退）
    candidates: Dict[str, str] = {}
    for src in src_dirs:
        for path in sorted(glob.glob(os.path.join(src, "speech_*.segments.json"))):
            vid = os.path.basename(path).replace(".segments.json", "")
            candidates.setdefault(vid, path)  # 优先第一个找到的 segments
        for path in sorted(glob.glob(os.path.join(src, "speech_*.json"))):
            if path.endswith(".segments.json") or "(1).json" in path:
                continue
            vid = os.path.basename(path).replace(".json", "")
            candidates.setdefault(vid, path)  # 无 segments 时回退原始转写

    total = 0
    for vid, path in sorted(candidates.items()):
        data = json.load(open(path, encoding="utf-8"))
        # 兼容 {segments:[...]} 与 [...]
        if isinstance(data, dict) and "segments" in data:
            data = data["segments"]
        out = [
            {"start": _s_start(s), "end": _s_end(s), "text": s["text"]}
            for s in data
        ]
        out_path = os.path.join(args.out, f"{vid}.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=1)
        total += len(out)
        print(f"[统一] {vid}: {len(out)} 个语义块 → {out_path}")

    print(f"\n共 {len(candidates)} 个视频、{total} 个语义块。")
    print("下一步评测：")
    print(f"  python scripts/run_eval.py --transcripts {args.out} "
          f"--gold data/eval/speech_dev.json --retriever bm25")


if __name__ == "__main__":
    main()
