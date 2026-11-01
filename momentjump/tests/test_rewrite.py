from src.retrieve.rewrite import QueryRewriter


def test_strip_filler():
    rw = QueryRewriter()
    q = rw.strip_filler("请问哪里讲了梯度消失的地方")
    assert "梯度消失" in q
    assert "请问" not in q
    assert "的地方" not in q


def test_expand_aliases():
    rw = QueryRewriter()
    q = rw.rewrite("多头注意力", expand_aliases=True)
    assert "multi-head attention" in q.lower()


def test_no_alias_expand():
    rw = QueryRewriter()
    q = rw.rewrite("梯度消失", expand_aliases=False)
    assert "vanishing" not in q.lower()


def test_rewrite_combined():
    rw = QueryRewriter()
    q = rw.rewrite("帮我找一下讲多头注意力的地方")
    assert "多头注意力" in q
    assert "帮我找" not in q
