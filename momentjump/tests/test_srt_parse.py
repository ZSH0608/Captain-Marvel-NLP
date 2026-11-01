from src.ingest.srt_parse import parse_srt

SRT = """1
00:00:01,000 --> 00:00:04,000
你好，世界

2
00:00:05,500 --> 00:00:08,250
第二句台词
（跨行）
"""


def test_parse_srt_count_and_time():
    items = parse_srt(SRT)
    assert len(items) == 2
    assert items[0].start == 1.0
    assert items[0].end == 4.0
    assert items[1].start == 5.5
    assert items[1].end == 8.25


def test_parse_srt_text():
    items = parse_srt(SRT)
    assert items[0].text == "你好，世界"
    assert "第二句台词" in items[1].text


def test_parse_srt_empty():
    assert parse_srt("") == []
