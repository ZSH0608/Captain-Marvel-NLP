# Speech 交付说明

日期：2026-11-08。范围：讲解型课程数据。在成员 1 已交付的 12 集之上，补齐队列、树、图。

## 交付文件

- `data/meta/speech/manifest.json`：在原 12 条后追加 speech_13–speech_19，现为 19 条。这 7 条已写入网盘地址 `https://pan.baidu.com/s/1cRHo76oDvo1Mykci7dq5lw?pwd=ufyb`，提取码 `ufyb`。mp4 在 `speech2/raw_videos`，转写在 `speech2/transcripts`。
- `data/meta/speech/alias_terms.json`：追加 15 组术语别名，现为 38 组。
- `data/eval/speech_dev.json`、`speech_test.json`：各追加 10 条（021–030），现为各 30 条。001–020 的题面和时间窗未改。
- 本文：`data/reports/member2_speech_交付说明.md`。

上述路径相对于 `momentjump/`。

## 网盘交付

speech_13–speech_19 的 mp4 在网盘目录 `speech2/raw_videos`（7 个），转写在 `speech2/transcripts`（7 个 `.json` 与 7 个 `.segments.json`）。

[新视频和转写下载](https://pan.baidu.com/s/1cRHo76oDvo1Mykci7dq5lw?pwd=ufyb)，提取码：`ufyb`。

## 规模自检与文件齐套表

| video_id | 内容标题 | 时长（秒） | mp4 | ASR / 分块数 | manifest 行 | gold 引用数 |
|---|---|---:|---|---:|---|---:|
| speech_13 | 队列的顺序实现 | 1006.91 | 本地有，已上传 | 514 / 48 | 有 | 3 |
| speech_14 | 队列的链式实现 | 565.21 | 本地有，已上传 | 276 / 27 | 有 | 2 |
| speech_15 | 双端队列 | 894.31 | 本地有，已上传 | 342 / 42 | 有 | 3 |
| speech_16 | 二叉树的定义和基本术语 | 766.68 | 本地有，已上传 | 394 / 37 | 有 | 3 |
| speech_17 | 二叉树的先中后序遍历 | 1388.35 | 本地有，已上传 | 578 / 63 | 有 | 3 |
| speech_18 | 树的定义和基本术语 | 917.21 | 本地有，已上传 | 505 / 43 | 有 | 3 |
| speech_19 | 图的基本概念 | 1839.45 | 本地有，已上传 | 964 / 87 | 有 | 3 |

本次 7 个视频，总时长 7378.12 秒（2.049 小时）。与成员 1 的 12 集（14510.933 秒）合计 19 个视频、21889.053 秒（6.080 小时），落在 5–10 小时以内。上表每个 `video_id` 至少被 1 条 gold 引用。

来源为王道计算机考研《数据结构》公开课免费考点讲解，`https://www.bilibili.com/video/BV1b7411N798`，分 P 依次为 24、25、26、43、46、41、58。

## 评测集统计

| 集合 | 总条数 | term | paraphrase | alias | hard |
|---|---:|---:|---:|---:|---:|
| dev | 30 | 10 | 7 | 7 | 6 |
| test | 30 | 7 | 8 | 7 | 8 |

别名表 38 组。本次新增的规范名：队列、循环队列、链队列、双端队列、二叉树、满二叉树、完全二叉树、二叉排序树、平衡二叉树、先序遍历、中序遍历、后序遍历、空树、无向图、有向图。

## 转写与检查

使用 faster-whisper small、CPU int8、中文识别，保留 ASR 片段和词级时间戳。
分块调用项目的 `chunk_pause_punctuation` 函数，以识别片段边界合并；并非严格固定时长窗口。
所有时间以秒表示。已检查 JSON 格式、视频引用、时间范围、时间顺序、片段编号和题目数量。
speech_test_021–030 已对照视频抽听，时间窗无误。test 后续用于评测时应冻结，不根据检索结果修改 gold；dev 可用于调参。


