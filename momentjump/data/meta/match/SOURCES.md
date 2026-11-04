# 赛事视频来源说明

负责人：2414166-滕鑫
整理日期：2026-11-02
所有数据路径相对于 momentjump/。时间一律为秒，零点对应各自本地MP4开头。

## match_badminton_01

- 标题：【央视解说】2019福州羽毛球公开赛混双八强赛:郑思维黄雅琼vs徐承宰蔡侑玎
- 来源：[B站原页面](https://b23.tv/im4ZuwI)
- 本地视频：`data/raw_videos/match/match_badminton_01.mp4`
- 本地实测时长：2000.400 秒；音轨数：1。
- 转写：`data/transcripts/match/match_badminton_01.json`，当前 419 段。
- A：郑思维/黄雅琼；B：徐承宰/蔡侑玎。
- 中文解说，faster-whisper medium 自动识别后由滕鑫回听校对。

## match_badminton_02

- 标题：（央视解说）2021世界羽联巡回赛总决赛 混双小组赛B组 邓俊文/谢影雪（中国香港）VS埃利斯/史密斯（英格兰）
- 来源：[B站原页面](https://b23.tv/EzKo1ME)
- 本地视频：`data/raw_videos/match/match_badminton_02.mp4`
- 本地实测时长：2473.320 秒；音轨数：1。
- 转写：`data/transcripts/match/match_badminton_02.json`，当前 391 段。
- A：邓俊文/谢影雪；B：埃利斯/史密斯。
- 中文解说，faster-whisper medium 自动识别后由滕鑫回听校对。

## 标注与交付约定

- 比分统一按A:B；winner_side表示当前这一分获胜方，不是整场赢家。
- 外国姓名可能存在音译差异。manifest采用成员提供标题的“埃利斯”，转写中的“埃里斯”指同一选手。
- 检索gold使用解说可支撑的时间窗；事件gold定位实际事件，不能机械套用ASR句段边界。
- match_e_003 的5:1由成员4回看画面确认；解说提及4:1，保留原文及JSON备注。
- dev用于开发；已人工确认的test作为最终评测基线，不因检索表现修改gold。
- 事件gold仅用于评测，不作为系统索引材料。
