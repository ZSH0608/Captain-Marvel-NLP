# 协作规范（Team Captain Marvel）

## 分支与提交

- **main 只收可运行的提交**；功能开发开 `feature/xxx` 分支，合并用 Pull Request。
- commit message 格式：`姓名：做了什么`（如 `张书晗：搭建检索核心与单元测试`）。
- 提交前跑一遍测试：`cd momentjump && python -m pytest tests/ -q`。

## 代码约定

- 所有核心模块放在 `momentjump/src/`，按 ingest / retrieve / eval / api 分层。
- 新增模块须带 docstring（中文），关键逻辑配单元测试 `momentjump/tests/`。
- 检索层与视频类别解耦：新增视频类别 = 新增 Ingest 源 + 评测集，**不碰检索核心**。

## 数据与评测

- **大文件不入库**（视频/音频/模型/向量），放 `momentjump/data/` 或外接硬盘（t7），
  已在 `.gitignore` 排除。
- **评测集 gold 入库**（`momentjump/data/eval/*.json`），这是团队成果。
- **dev / test 分离**：开发期反复调的 query 放 dev；test 冻结，只在最终报告跑一次，
  避免过拟合。

## 模块分工

| 成员 | 负责 |
|------|------|
| 张书晗 | 检索核心（hybrid/rerank/rewrite）+ 架构 |
| 滕鑫 | Ingest（asr/chunking/索引） |
| 李子非 | 数据与评测（评测集、metrics、消融） |
| 付子轩 | 系统与 Demo（api/streamlit/部署） |
| 赵悦娇 | 剧情/赛事接入（srt/场景/事件）+ 报告 |

> 分工以最终 Proposal 为准，可随进度调整。
