from src.ingest.event_spotting import rule_based_spot
from src.segment import TimedText


def test_point_start():
    events = rule_based_spot([TimedText(53.1, 53.82, "黄雅琼发球")])
    assert events[0]["event_type"] == "point_start"


def test_score_change():
    events = rule_based_spot([TimedText(218.71, 220.23, "开局取得了4比1的领先")])
    assert events[0]["event_type"] == "score_change"
    assert events[0]["score_after"] == "4:1"


def test_point_end():
    events = rule_based_spot([TimedText(100.0, 102.0, "胡连芳这个高点拿得漂亮，得分了")])
    assert events[0]["event_type"] == "point_end"


def test_winner_side_a():
    events = rule_based_spot(
        [TimedText(1.0, 2.0, "黄雅琼杀球得分")],
        side_a_terms=["黄雅琼", "郑思维"],
        side_b_terms=["徐承宰", "蔡侑玎"],
    )
    assert events[0]["event_type"] == "point_end"
    assert events[0]["winner_side"] == "A"
