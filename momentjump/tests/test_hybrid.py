from src.retrieve.hybrid import reciprocal_rank_fusion, weighted_fusion


def test_rrf_contains_all():
    fused = reciprocal_rank_fusion([["a", "b", "c"], ["b", "a", "d"]], k=60)
    ids = {d for d, _ in fused}
    assert ids == {"a", "b", "c", "d"}


def test_rrf_top_rank_wins():
    fused = reciprocal_rank_fusion([["a", "b"], ["a", "b"]], k=60)
    assert fused[0][0] == "a"


def test_rrf_scores_positive():
    fused = reciprocal_rank_fusion([["a", "b"]], k=60)
    assert all(s > 0 for _, s in fused)


def test_weighted_fusion():
    fused = weighted_fusion([("a", 0.9), ("b", 0.5)], [("b", 0.8), ("a", 0.3)], alpha=0.5)
    ids = [d for d, _ in fused]
    assert set(ids) == {"a", "b"}
