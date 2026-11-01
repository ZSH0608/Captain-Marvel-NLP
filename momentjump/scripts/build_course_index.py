"""讲解型（课程）索引构建脚本。

流程：videos/*.mp4 → 抽音频 → ASR 转写 → 停顿边界切分 → 嵌入 → 建索引。

用法：:

    python scripts/build_course_index.py --video-dir data/raw_videos --out data/transcripts
"""
from __future__ import annotations

import argparse


def main() -> None:
    parser = argparse.ArgumentParser(description="构建讲解型课程索引")
    parser.add_argument("--video-dir", default="data/raw_videos")
    parser.add_argument("--out", default="data/transcripts")
    args = parser.parse_args()
    print(f"[TODO] 讲解型索引构建：{args.video_dir} -> {args.out}")
    print("步骤：extract_audio -> asr.transcribe -> chunk(pause_punctuation) -> DenseRetriever.encode -> IndexStore.save")


if __name__ == "__main__":
    main()
