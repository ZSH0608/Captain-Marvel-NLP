import pytest

from src.segment import Segment, TimedText


def test_segment_valid():
    s = Segment("id", "speech", "v1", "第3讲", 10.0, 20.0, "多头注意力")
    assert s.duration == pytest.approx(10.0)
    assert s.center == pytest.approx(15.0)


def test_segment_invalid_domain():
    with pytest.raises(ValueError):
        Segment("id", "bad", "v1", "t", 0.0, 10.0, "x")


def test_segment_invalid_time_order():
    with pytest.raises(ValueError):
        Segment("id", "speech", "v1", "t", 20.0, 10.0, "x")


def test_segment_empty_text():
    with pytest.raises(ValueError):
        Segment("id", "speech", "v1", "t", 0.0, 10.0, "   ")


def test_segment_roundtrip():
    s = Segment("id", "dialogue", "v1", "t", 1.0, 2.0, "对白", "subtitle", {"episode": 3})
    assert Segment.from_dict(s.to_dict()) == s


def test_timedtext():
    t = TimedText(1.0, 4.0, "台词")
    assert t.duration == 3.0
