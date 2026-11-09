"""剧情型（剧集字幕）索引构建脚本。

流程：SRT 解析 → 对话块合并 → 转写 JSON（供 run_eval.py 检索评测）。

用法：:

    python scripts/build_drama_index.py --srt-dir data/subtitles --out data/transcripts/drama
"""
from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.ingest.chunking import chunk_fixed
from src.ingest.srt_parse import parse_srt_file


def main() -> None:
    parser = argparse.ArgumentParser(description="构建剧情型字幕索引")
    parser.add_argument("--srt-dir", default="data/subtitles")
    parser.add_argument("--out", default="data/transcripts/drama")
    parser.add_argument("--chunk-sec", type=float, default=15.0, help="对话块合并时长")
    args = parser.parse_args()

    os.makedirs(args.out, exist_ok=True)
    for fname in sorted(os.listdir(args.srt_dir)):
        if not fname.endswith(".srt"):
            continue
        vid = fname[:-4]  # 去 .srt 后缀
        items = parse_srt_file(os.path.join(args.srt_dir, fname))
        if not items:
            print(f"[警告] {fname} 无有效字幕")
            continue
        # 对话块合并：固定窗合并短对话（剧集型对白无句末标点，不适合停顿切分）
        blocks = chunk_fixed(items, window_sec=args.chunk_sec)
        out_path = os.path.join(args.out, f"{vid}.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(
                [{"start": b.start, "end": b.end, "text": b.text} for b in blocks],
                f,
                ensure_ascii=False,
                indent=2,
            )
        print(f"[转换] {vid}: {len(items)} 句字幕 → {len(blocks)} 个对话块 → {out_path}")

    print("\n下一步评测：")
    print(f"  python scripts/run_eval.py --transcripts {args.out} "
          f"--gold data/eval/drama_dev.json --retriever bm25")


if __name__ == "__main__":
    main()
