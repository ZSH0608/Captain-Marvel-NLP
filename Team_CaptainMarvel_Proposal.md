---
title: "MomentJump: Natural Language Semantic Retrieval and Timestamp Localization for General Web Videos"
author: "Team Captain Marvel · Track B (Demonstration)"
geometry: margin=0.7in
fontsize: 11pt
mainfont: "Times New Roman"
header-includes:
  - \usepackage{booktabs}
  - \usepackage{longtable}
  - \setlength{\parskip}{0.35em}
  - \setlength{\parindent}{0pt}
---

**NLP Course Project Proposal · Track B: Demonstration**  
**Team:** Captain Marvel

# 1. Project Title

**MomentJump: Natural Language Semantic Retrieval and Timestamp Localization for General Web Videos.** The system covers three content regimes—**speech-centric**, **dialogue-centric**, and **event-centric** videos—whose primary signals are speech (ASR), dialogue subtitles, and commentary plus discrete events, respectively.

# 2. Team Members & Responsibilities

| Member / ID | Role | Responsibilities |
|:---|:---|:---|
| Zhang Shuhan / 2413157 | Lead · Retrieval Core | Hybrid retrieval (Dense+BM25+RRF), Cross-Encoder reranking, query rewriting; system architecture |
| Teng Xin / 2414166 | Ingest Pipeline | ffmpeg audio extraction, faster-whisper ASR, chunking (fixed/sliding/pause-boundary), multi-signal indexing |
| Li Zifei / 2312183 | Data & Evaluation | Corpus curation, query→gold timestamp annotation, metrics (R@K / mIoU / temporal error), unified ablations |
| Fu Zixuan / 2313715 | System & Demo | FastAPI backend, Streamlit UI, domain switching, player seek, deployment & demo recording |
| Zhao Yuejiao / 2313650 | Domain Adapters · Report | SRT/scene blocks, event-log alignment, failure analysis, README / report / slides |

# 3. Background & Motivation

Web videos are information-dense yet hard to navigate: users seeking “the few seconds on a concept,” “a specific line,” or “a goal moment” often rely on titles, chapter markers, or scrubbing. Keyword search and platform chapters operate at title/episode granularity and rarely support second-level localization. The ACL 2025 Demo **LECTURE4ALL** shows that ASR transcription, semantic chunking, and dense retrieval enable precise timestamping for lecture videos, but evaluation focuses on usability (SUS), **lacks standard IR metrics**, and centers on English, single-domain content.

Our motivation is to treat lectures, drama, and sports not as isolated applications but as three content-signal regimes, and to build a **unified text-segment retrieval framework** evaluated with standard IR metrics across all three. We will implement **chunking strategies, hybrid retrieval, query rewriting, Cross-Encoder reranking, and an automatic evaluation suite**, yielding a demonstrable, general, and measurable system.

# 4. Problem Definition / Research Questions

**Task.** Given a natural-language query and a video corpus, return the most relevant clips `(video_id, start_sec, end_sec, snippet)` for one-click playback.  
**Input.** Chinese/English queries (colloquial questions, technical phrases, plot descriptions, event descriptions).  
**Output.** A Top-K ranked list with timestamps, matched text, confidence, and play links.  
**Success criterion.** Predicted span IoU ≥ θ with gold, or predicted center within gold ± δ (δ = 10s / 15s).

**Generality.** All domains map to a unified `Segment` (`domain` ∈ {speech, dialogue, event}). The retrieval stack is domain-agnostic; only ingest signal sources differ (ASR / subtitles / commentary+events). Scope covers videos with transcribable text signals; pure visual, textless content is out of core scope.

- **RQ1 (Generality / effectiveness):** Does unified Hybrid (Dense+BM25+RRF) consistently outperform Dense-only and BM25-only across the three domains?
- **RQ2 (Segmentation):** How do fixed, sliding, and pause/punctuation chunking affect localization precision and recall? Does the best strategy differ by domain?
- **RQ3 (Signal availability):** How do speech / dialogue / commentary+event signals affect retrieval, and where does the framework fail?
- **RQ4 (Optional gains):** What gains do query rewriting and Cross-Encoder reranking bring in each domain?

# 5. System Design & Technical Approach

## 5.1 System Functions

1. Domain switching (speech / dialogue / event) with NL search returning Top-K clips.  
2. Result cards with title, timecode, highlighted transcript, and similarity; click-to-seek from `start_sec`.  
3. Side-by-side ablation panel (disable Hybrid / disable rerank) to visualize module gains.

## 5.2 Technical Architecture

**Pipeline:** video/subtitles/commentary → **Ingest** (ffmpeg → faster-whisper ASR / SRT parsing / event-log alignment → chunking → BGE-M3 embedding) → **Index** (FAISS + BM25 + SQLite metadata) → **Retrieval** (query rewrite → Hybrid → rerank → aggregation) → **Service** (FastAPI) → **UI** (Streamlit + HTML5 seek). Domains share a common `Segment` schema; retrieval is category-agnostic, with domain differences isolated in ingest.

**Stack:** faster-whisper (Chinese ASR); BGE-M3 / bge-base-zh (embeddings); bge-reranker-base; FAISS + rank_bm25; FastAPI + Streamlit.

## 5.3 Implementation Plan

**In-house modules:** (i) Chinese chunking ablations (fixed / sliding / pause–punctuation); (ii) Hybrid retrieval with RRF fusion; (iii) colloquial query rewriting; (iv) Cross-Encoder reranking and comparisons; (v) unified evaluation sets and automated metrics across three domains.

**Reusable components:** faster-whisper (ASR API only), pretrained BGE embedding/reranker weights, FAISS/rank_bm25, Streamlit/FastAPI frameworks—with clear reuse boundaries in the README.

**Data (rights-cleared):** speech-centric open lectures / self-recorded talks (3–10 h); dialogue-centric short dramas or public samples with custom SRT (2–5 clips); event-centric short highlights with 20–40 annotated events (incl. esports commentary). **40–80** `query→gold timestamp` items per domain.

## 5.4 Evaluation Plan

**Metrics:** Recall@1/@3/@5; mIoU; median absolute start-time error. Hit rule: IoU or center within δ = 10s / 15s.

**Baselines / ablations (identical suite on all three domains):** BM25-only → Dense-only → Hybrid → Hybrid+Rerank; plus chunking and w/ vs w/o query rewrite. Cross-domain consistency of gains serves as evidence of generality.

# 6. Expected Outcomes

1. Runnable system + Web Demo (README with environment, commands, sample queries): domain switch, search → Top-K → seek-to-play.  
2. Experimental report: unified R@K / temporal error / mIoU, ablations, generality claims, and failure cases.  
3. Source code and configs (`requirements.txt`, `configs/default.yaml`).  
4. **Target:** Hybrid+Rerank outperforms Dense-only and BM25-only on R@K and temporal error across domains; end-to-end reproducibility and live demo.

# 7. Project Timeline

| Phase | Milestone | Tasks |
|:---|:---|:---|
| Oct 2026 | Spec freeze | Data & rights clearance, environment, v0 eval sets, architecture freeze |
| Mid-Nov 2026 | MVP (midterm-ready) | ≥3 speech videos transcribed & indexed; Dense/BM25 + Web seek; initial R@K; domain-agnostic retrieval & eval scripts |
| End of term | Full delivery | Dialogue/event adapters; full Hybrid+Rerank+rewrite ablations; report, slides, demo video |

# References

1. Hannemann et al. *LECTURE4ALL: A Lightweight Approach to Precise Timestamp Detection in Online Lecture Videos.* ACL 2025 Demo. https://aclanthology.org/2025.acl-demo.59/
2. Yuan et al. *MomentSeeker: A Task-Oriented Benchmark for Long-Video Moment Retrieval.* NeurIPS 2025 D&B.
3. *MomentBench: Corpus-level Video Moment Retrieval.* https://github.com/mixpeek/momentbench
4. *SceneRAG: Scene-level RAG for Video Understanding.* arXiv:2506.07600.
5. *SoccerNet-Echoes.* arXiv:2405.07354.
6. Chen et al. *BGE-M3 (FlagEmbedding).* https://github.com/FlagOpen/FlagEmbedding
7. *faster-whisper.* https://github.com/SYSTRAN/faster-whisper
8. *LecTrack-ZH: Semantic Search over Chinese Lectures.* https://github.com/nyveth/LecTrack-ZH
9. Adcock et al. *TalkMiner: A Search Engine for Online Lecture Video.* ACM MM 2010.
10. Pujol et al. *Beyond Caption-Based Queries for Video Moment Retrieval.* CVPR 2026.
