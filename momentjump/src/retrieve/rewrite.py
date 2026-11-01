"""Query 改写：口语问句 → 检索友好表述 + 别名/同义扩展。

讲解型的关键语义难点是「别名/同义」：讲解者一贯称某概念为 a，用户用别名 b
查询（如「多头注意力」 vs 「multi-head attention」）。本模块用规则 + 别名表桥接。
"""
from __future__ import annotations

import re
from typing import Dict, List, Optional

# 口语疑问词 / 冗余填充词（会被剔除）
_STOP_PATTERNS = [
    "请问", "我想知道", "我想问", "有没有讲过", "有没有", "帮我找",
    "哪里讲了", "哪里讲到", "讲到", "讲一下", "说说", "解释一下",
    "是什么", "怎么", "如何", "能不能", "可不可以",
    "的地方", "的部分", "那一秒", "那一段", "的时刻",
]

# 默认别名表（可外部覆盖/扩充；讲解型术语别名）
DEFAULT_ALIASES: Dict[str, List[str]] = {
    "多头注意力": ["multi-head attention", "multihead attention", "多头自注意力"],
    "自注意力": ["self-attention", "self attention"],
    "交叉熵": ["cross-entropy", "cross entropy", "交叉熵损失"],
    "梯度消失": ["vanishing gradient", "梯度弥散"],
    "梯度爆炸": ["exploding gradient"],
    "词向量": ["word embedding", "词嵌入"],
    "transformer": ["Transformer", "transformers"],
}


class QueryRewriter:
    """规则 + 别名表的口语 query 改写器。"""

    def __init__(self, aliases: Optional[Dict[str, List[str]]] = None) -> None:
        self.aliases = aliases if aliases is not None else DEFAULT_ALIASES

    def strip_filler(self, query: str) -> str:
        q = query.strip()
        for p in _STOP_PATTERNS:
            q = q.replace(p, " ")
        return re.sub(r"\s+", " ", q).strip()

    def expand_aliases(self, query: str) -> str:
        parts = [query]
        for key, variants in self.aliases.items():
            if key.lower() in query.lower():
                parts.extend(variants)
        return " ".join(parts)

    def rewrite(self, query: str, expand_aliases: bool = True) -> str:
        q = self.strip_filler(query)
        if expand_aliases:
            q = self.expand_aliases(q)
        return q
