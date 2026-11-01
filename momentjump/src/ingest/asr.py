"""ASR：ffmpeg 抽音频 + faster-whisper 转写（讲解型/赛事型信号来源）。

依赖：ffmpeg（系统命令）、faster-whisper（pip）。模型下载见 README 与
`工作进度.md` 的待办清单。
"""
from __future__ import annotations

import subprocess
from typing import List

from ..segment import TimedText


def extract_audio(video_path: str, out_wav: str, sample_rate: int = 16000) -> None:
    """用 ffmpeg 抽取 16k 单声道 wav（faster-whisper 推荐输入）。"""
    cmd = [
        "ffmpeg", "-y", "-i", video_path,
        "-ar", str(sample_rate), "-ac", "1", "-vn", out_wav,
    ]
    subprocess.run(cmd, check=True, capture_output=True)


def transcribe(
    audio_path: str,
    model_size: str = "medium",
    language: str = "zh",
    device: str = "auto",
    compute_type: str = "int8",
) -> List[TimedText]:
    """faster-whisper 转写，返回句级 `TimedText` 列表（保留时间戳）。"""
    from faster_whisper import WhisperModel  # 延迟导入，避免硬依赖

    model = WhisperModel(model_size, device=device, compute_type=compute_type)
    segments, _info = model.transcribe(audio_path, language=language)
    out: List[TimedText] = []
    for seg in segments:
        text = seg.text.strip()
        if text:
            out.append(TimedText(seg.start, seg.end, text))
    return out
