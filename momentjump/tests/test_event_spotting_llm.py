from src.ingest.event_spotting_llm import _parse_events, _window_to_input


def test_parse_plain_json():
    raw = '[{"event_type":"point_start","start_sec":53.1,"end_sec":53.82,"winner_side":null,"score_after":null,"evidence_text":"发球"}]'
    evs = _parse_events(raw)
    assert len(evs) == 1
    assert evs[0]["event_type"] == "point_start"
    assert evs[0]["start_sec"] == 53.1


def test_parse_markdown_codeblock():
    raw = '```json\n[{"event_type":"score_change","start_sec":218.71,"end_sec":220.23,"winner_side":"A","score_after":"4:1","evidence_text":"4比1"}]\n```'
    evs = _parse_events(raw)
    assert len(evs) == 1
    assert evs[0]["score_after"] == "4:1"


def test_parse_with_thinking_prefix():
    # 模拟 deepseek-r1 思维链 + 最终 JSON
    raw = "一些思维过程…… 输出如下：[{\"event_type\":\"point_end\",\"start_sec\":230.0,\"end_sec\":232.5,\"winner_side\":\"A\",\"score_after\":null,\"evidence_text\":\"杀球得分\"}]"
    evs = _parse_events(raw)
    assert len(evs) == 1
    assert evs[0]["event_type"] == "point_end"


def test_parse_invalid_returns_empty():
    assert _parse_events("没有 JSON") == []
    assert _parse_events("") == []


def test_window_to_input():
    w = [{"start": 1.0, "end": 2.0, "text": "发球"}]
    s = _window_to_input(w)
    assert '"text": "发球"' in s
    assert '"start": 1.0' in s
