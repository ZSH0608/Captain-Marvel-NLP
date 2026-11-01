"""Streamlit 前端：搜索框 → Top-K 结果 → 一键跳转播放（MVP）。

用法：:

    streamlit run app/streamlit_app.py
"""
from __future__ import annotations

import streamlit as st

st.set_page_config(page_title="MomentJump", layout="wide")
st.title("MomentJump · 自然语言 → 视频时间戳")

DOMAINS = {"讲解型": "speech", "剧情型": "dialogue", "赛事型": "event"}
SAMPLE_QUERIES = {
    "讲解型": ["讲 Transformer 多头注意力的地方", "交叉熵损失函数怎么定义"],
    "剧情型": ["男主在雨里分手", "反派揭露身份"],
    "赛事型": ["比分变成 2:1", "终场前绝杀"],
}

col1, col2 = st.columns([1, 3])
with col1:
    domain_label = st.selectbox("视频类别", list(DOMAINS.keys()))
with col2:
    query = st.text_input("输入你想找的内容", placeholder="例如：讲梯度消失的地方")

if st.button("搜索") or query:
    q = query or SAMPLE_QUERIES[domain_label][0]
    st.info(f"查询：{q}（domain={DOMAINS[domain_label]}）")
    # TODO: 调用后端 /api/search，渲染结果卡。占位示例：
    st.warning("检索后端尚未接入 IndexStore——请先运行 scripts/ 构建索引，并在 server.py 注入 store。")
    st.caption("接入后：结果卡展示标题 / 时间码 / 字幕高亮 / 相似度，点击从 start_sec 起播。")
