# MomentJump

面向通用网络视频的自然语言语义检索与时间戳定位系统（NLP 课程大作业 · Track B）。

一句话：输入自然语言 query，返回视频里最相关的那几秒，一键跳转播放。
三类视频（统一检索内核，差异在 Ingest 信号来源）：

| 类别 | 信号 | 索引单元 | 检索策略 |
|------|------|---------|---------|
| 讲解型 speech | ASR | 停顿边界语义块 | 关键词为主 + 别名/同义语义补强 |
| 剧情型 dialogue | 字幕/对白 | 场景（多块对话聚合） | 场景级语义检索为主 |
| 赛事型 event | 解说 + 事件 | 事件 + 解说片段 | 事件检索 + 解说检索 |

完整方案见仓库根目录 `项目完整方案.md`，数据来源见 `可用来源.md`。

## 目录结构

```
momentjump/
├── src/
│   ├── segment.py            # Segment / TimedText 数据单元
│   ├── ingest/               # 离线入库：asr / srt_parse / chunking / index_builder
│   ├── retrieve/             # 在线检索：bm25 / dense / hybrid / rewrite / rerank
│   ├── eval/                 # 评测：R@K / mIoU / 时间误差
│   └── api/                  # FastAPI 服务
├── app/streamlit_app.py      # Streamlit 前端
├── scripts/                  # build_course_index / build_drama_index / run_eval
├── tests/                    # 单元测试
├── configs/default.yaml      # 默认配置
└── data/                     # 数据（视频/转写/字幕/事件/评测集，大文件不入库）
```

## 安装

```bash
pip install -r requirements.txt
```

- **ASR** 需额外下载 Whisper 模型（faster-whisper 会自动缓存，建议设置缓存到外接硬盘）：
  ```bash
  export HF_HOME=/Volumes/T7/hf-cache   # 示例：把模型缓存放到 t7 硬盘
  ```
- 向量编码 / 重排需联网下载 BGE 权重，首次运行时自动缓存。

## 运行单元测试

```bash
cd momentjump
python -m pytest tests/ -v
```

当前 29 个测试全部通过（segment / chunking / srt_parse / hybrid / rewrite / metrics）。

## 快速开始（数据就绪后）

1. 准备视频/字幕到 `data/`，先跑通讲解型：
   ```bash
   python scripts/build_course_index.py --video-dir data/raw_videos --out data/transcripts
   ```
2. 评测：
   ```bash
   python scripts/run_eval.py --eval data/eval/course_dev.json --index data/transcripts
   ```
3. 启动 Demo（前端 + 后端接入 IndexStore 后）：
   ```bash
   streamlit run app/streamlit_app.py
   ```

## 自研 vs 复用边界

**自研模块**（必须自己写 / 大幅改造）：chunking（停顿边界 + 固定/滑动消融）、
场景聚合、Hybrid（RRF 融合）、query 改写（别名/同义）、Cross-Encoder 重排接入、
统一评测流水线、赛事解说事件识别。

**复用组件**：faster-whisper（ASR）、BGE 系列预训练权重（embedding/rerank）、
rank_bm25 / numpy（索引）、FastAPI / Streamlit（服务与 UI）。

> 合规要求：不得整仓 fork 开源项目换皮；README/报告需区分第三方组件与自研模块。
