"""剧情型（剧集字幕）索引构建脚本。

流程：SRT 解析 → 对话块合并 → 场景聚合 → 嵌入 → 建索引。

用法：:

    python scripts/build_drama_index.py --srt-dir data/subtitles --out data/subtitles
"""
from __future__ import annotations

import argparse


def main() -> None:
    parser = argparse.ArgumentParser(description="构建剧情型字幕索引")
    parser.add_argument("--srt-dir", default="data/subtitles")
    parser.add_argument("--out", default="data/subtitles")
    args = parser.parse_args()
    print(f"[TODO] 剧情型索引构建：{args.srt_dir} -> {args.out}")
    print("步骤：parse_srt_file -> 对话块合并(8-20s) -> 场景聚合 -> DenseRetriever.encode -> IndexStore.save")


if __name__ == "__main__":
    main()
