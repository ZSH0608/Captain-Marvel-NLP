# 成员4赛事型数据交付说明

负责人：滕鑫；日期：2026-11-02。
本报告对应成员4负责的赛事型数据与评测集。

## 规模自检

| 视频ID | 时长（秒） | MP4 | 转写 | 清单行 | 检索gold引用 | 事件gold引用 |
|---|---:|---|---|---|---:|---:|
| match_badminton_01 | 2000.400 | 有 | 有（419段） | 有 | 30 | 15 |
| match_badminton_02 | 2473.320 | 有 | 有（391段） | 有 | 30 | 15 |

共2场羽毛球混双材料，总时长 4473.720 秒（约 74.56 分钟）。

## 检索评测统计

| 划分 | 条数 | event | paraphrase | hard |
|---|---:|---:|---:|---:|
| dev | 30 | 26 | 3 | 1 |
| test | 30 | 23 | 3 | 4 |

合计60条，满足60–80条及dev/test各至少30条要求。以event为主，并覆盖paraphrase和hard。
用户已确认回听修改并授权导出。导出程序校验了必填字段、ID唯一性、数值秒数、视频范围及划分一致性。

## 事件评测统计

| event_type | 条数 |
|---|---:|
| point_start | 4 |
| other | 5 |
| score_change | 10 |
| point_end | 11 |

合计30条，满足20–40条及建议30条。winner_side：A=17，B=9，null=4。
比分字段非空 12/30（40%）；未确认或不适用部分保留null，不补猜。
match_e_003：画面核实比分5:1，解说原文4:1，差异已写入事件JSON备注。

## 交付清单

- `data/meta/match/manifest.json`：2条来源与本地文件记录。
- `data/meta/match/SOURCES.md`：来源、A/B映射与使用说明。
- `data/eval/match_dev.json`、`match_test.json`：UTF-8 JSON数组，各30条。
- `data/eval/match_events_gold.json`：UTF-8 JSON数组，30条，仅用于评测。
- `data/transcripts/match/<video_id>.json`：本地校对转写；是否入库待团队协商。
- `data/raw_videos/match/<video_id>.mp4`：仅本地/网盘，禁止Git提交。

## 评测基线文件摘要

test人工标注已导出为当前评测基线。以下SHA-256用于核对版本，不表示已设置文件写保护。

- `match_dev.json`：`4c01595b85fc6ba6a80dbb0ccc3b76f54878fb506aa42378b696c487bc95f471`
- `match_test.json`：`0d62b1bbfd084ca09e7f093908cf109380eeab3779a425e1aec396056b91e0b1`
- `match_events_gold.json`：`5ade2d560ed621473d8bacaa6be53d41a56ef40438fe26319b404d179796b276`
