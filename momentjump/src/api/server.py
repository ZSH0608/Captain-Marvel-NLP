"""FastAPI 检索服务。

用法：:

    uvicorn src.api.server:app --host 0.0.0.0 --port 8000

依赖：fastapi、uvicorn（见 requirements.txt）。
"""
from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel


class SearchRequest(BaseModel):
    query: str
    domain: str = "speech"  # speech | dialogue | event
    top_k: int = 5
    use_rerank: bool = False


class SearchResult(BaseModel):
    video_id: str
    title: str
    start_sec: float
    end_sec: float
    snippet: str
    score: float
    play_url: str


def _make_app(store, reranker=None):
    """由 IndexStore 构建 FastAPI app（便于测试注入）。"""
    from fastapi import FastAPI

    app = FastAPI(title="MomentJump", version="0.1.0")

    @app.get("/health")
    def health():
        return {"status": "ok", "n_segments": len(store.segments)}

    @app.post("/api/search", response_model=List[SearchResult])
    def search(req: SearchRequest):
        # 1) Hybrid 召回（这里用 BM25 作为关键词通道；Dense 需先编码 query）
        bm25_hits = store.bm25.search(req.query, top_k=max(req.top_k * 2, 10))
        candidates = [store.segments[i] for i, _ in bm25_hits]

        # 2) 可选重排
        if reranker is not None and req.use_rerank and candidates:
            scored = reranker.rerank(req.query, [c.text for c in candidates], top_n=req.top_k)
            candidates = [candidates[i] for i, _ in scored]

        results = []
        for c in candidates[: req.top_k]:
            results.append(
                SearchResult(
                    video_id=c.video_id,
                    title=c.title,
                    start_sec=c.start_sec,
                    end_sec=c.end_sec,
                    snippet=c.text[:120],
                    score=0.0,
                    play_url=f"/media/{c.video_id}.mp4#t={c.start_sec}",
                )
            )
        return results

    return app


# 默认入口：由外部脚本注入 IndexStore 后再启动（见 scripts/）。
app = None
