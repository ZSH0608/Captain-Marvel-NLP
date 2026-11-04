# Speech 交付说明

日期：2026-11-04。范围：讲解型课程数据。

## 交付文件

- `data/meta/speech/manifest.json`：12 条视频清单，包含时长、语言、路径、网盘地址和使用说明。
- `data/meta/speech/alias_terms.json`：23 组术语别名。
- `data/eval/speech_dev.json`、`speech_test.json`：各 20 条检索题。
- 本文：`data/reports/member12_speech_交付说明.md`。

上述路径相对于 `momentjump/`。分工文件对汇报名有两种写法，本次采用详细要求中的 `member12_speech_交付说明.md`。

## 网盘交付

[原视频和转写下载](https://pan.baidu.com/s/1lAaeM9QOCCghBPRWIVxl2A?pwd=4fnw)，提取码：`4fnw`。


## 规模自检与文件齐套表

| video_id | 内容标题 | 时长（秒） | mp4 | ASR / 分块数 | manifest 行 | gold 引用数 |
|---|---|---:|---|---:|---|---:|
| speech_01 | 线性表的定义与基本操作 | 1064.811 | 本地有 | 491 / 50 | 有 | 5 |
| speech_02 | 顺序表的定义与实现 | 1405.227 | 本地有 | 434 / 64 | 有 | 6 |
| speech_03 | 顺序表的插入与删除 | 1253.141 | 本地有 | 616 / 60 | 有 | 2 |
| speech_04 | 顺序表的查找 | 753.984 | 本地有 | 280 / 35 | 有 | 2 |
| speech_05 | 单链表的定义与初始化 | 721.045 | 本地有 | 333 / 34 | 有 | 4 |
| speech_06 | 单链表的插入与删除 | 1390.229 | 本地有 | 609 / 65 | 有 | 1 |
| speech_07 | 单链表的查找与求表长 | 629.376 | 本地有 | 292 / 30 | 有 | 2 |
| speech_08 | 单链表的建立：头插法与尾插法 | 813.717 | 本地有 | 297 / 38 | 有 | 4 |
| speech_09 | 数组与特殊矩阵的压缩存储 | 1663.637 | 本地有 | 912 / 79 | 有 | 2 |
| speech_10 | 栈的应用：表达式求值 | 1903.147 | 本地有 | 875 / 90 | 有 | 5 |
| speech_11 | 字符串模式匹配：KMP 算法 | 1497.621 | 本地有 | 694 / 70 | 有 | 3 |
| speech_12 | 串的定义与基本操作 | 1414.997 | 本地有 | 569 / 66 | 有 | 4 |

共 12 个视频，总时长 14510.933 秒（4.031 小时）。

## 评测集统计

| 集合 | 总条数 | term | paraphrase | alias | hard |
|---|---:|---:|---:|---:|---:|
| dev | 20 | 5 | 5 | 5 | 5 |
| test | 20 | 5 | 5 | 5 | 5 |

## 转写与检查

使用 faster-whisper small、CPU int8、中文识别，保留 ASR 片段和词级时间戳。
分块调用项目的 `chunk_pause_punctuation` 函数，以识别片段边界合并；并非严格固定时长窗口。
所有时间以秒表示。已检查 JSON 格式、视频引用、时间范围、时间顺序、片段编号和题目数量。
test 后续用于评测时应冻结，不根据检索结果修改 gold；dev 可用于调参。

## 建议提交命令

在仓库根目录执行：

```powershell
git add momentjump/data/meta/speech momentjump/data/eval/speech_dev.json momentjump/data/eval/speech_test.json momentjump/data/reports/member12_speech_交付说明.md
git diff --cached --stat
git commit -m "Add speech dataset metadata and retrieval evaluation"
git push
```

本次未执行 git add、commit 或 push。
