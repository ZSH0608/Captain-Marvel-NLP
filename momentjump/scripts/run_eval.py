"""统一评测脚本：R@K / mIoU / 时间误差 + 消融对比。

输入：评测集 JSON（query + video_id + gold_start + gold_end）。
用法：:

    python scripts/run_eval.py --eval data/eval/course_dev.json --index data/transcripts
"""
from __future__ import annotations

import argparse


def main() -> None:
    parser = argparse.ArgumentParser(description="运行检索评测")
    parser.add_argument("--eval", default="data/eval/course_dev.json")
    parser.add_argument("--index", default="data/transcripts")
    args = parser.parse_args()
    print(f"[TODO] 评测：{args.eval} @ {args.index}")
    print("指标：recall_at_k / median_time_error / mean_iou；消融：BM25-only / Dense-only / Hybrid / Hybrid+Rerank")


if __name__ == "__main__":
    main()
