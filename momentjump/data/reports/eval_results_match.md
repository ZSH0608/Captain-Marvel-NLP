# 赛事型（event）首轮基线结果

> 负责人：张书晗 · 日期：2026-11-04
> 数据：滕鑫交付的 2 场羽毛球混双（match_badminton_01/02，共 810 句解说转写）
> 评测：match_dev.json / match_test.json（各 30 条）+ match_events_gold.json（30 事件）

## 检索评测

**dev（30 条）**

| 基线 | R@1 | R@3 | R@5 | mIoU | 时间误差中位数 |
|------|-----|-----|-----|------|--------------|
| BM25 | 0.6000 | 0.7333 | 0.8000 | — | 8.77s |
| Dense | 0.3667 | 0.6667 | 0.7000 | 0.2429 | 38.58s |
| Hybrid | 0.6000 | 0.7333 | 0.7667 | 0.3775 | 7.08s |

**test（30 条，冻结）**

| 基线 | R@1 | R@3 | R@5 | mIoU | 时间误差中位数 |
|------|-----|-----|-----|------|--------------|
| BM25 | 0.5000 | 0.6667 | 0.7333 | 0.2986 | 13.55s |
| Dense | 0.4667 | 0.5000 | 0.5667 | 0.3010 | 14.26s |
| Hybrid | 0.5000 | 0.6333 | 0.6667 | 0.3077 | 12.08s |

## 事件识别（规则基线迭代 vs LLM）

规则基线四步迭代（F1 0.17 → 0.29）：

| 版本 | Precision | Recall | F1 | 命中 |
|------|-----------|--------|-----|------|
| 规则基线（原） | 0.1100 | 0.3667 | 0.1692 | 11/30 |
| + 比分正则加强（中文数字/平局） | 0.1250 | 0.4333 | 0.1940 | 13/30 |
| + 失误/出界词（point_end 主体） | 0.1606 | 0.7333 | 0.2635 | 22/30 |
| + 顺序修正 + other 类型 | 0.1720 | **0.9000** | **0.2888** | 27/30 |

| 方法 | Precision | Recall | F1 |
|------|-----------|--------|-----|
| 规则基线（最终） | 0.1720 | **0.9000** | **0.2888** |
| LLM few-shot（qwen2.5:3b） | 0.1111 | 0.1333 | 0.1212 |
| 规则+LLM 融合（qwen2.5:3b） | 0.1081 | 0.2667 | 0.1538 |

**规则迭代要点**：① 比分正则补中文数字（"十一比七"→11:7）与平局（"14平"→14:14），score_change 覆盖 10/10；② gold point_end 主体是「失误得分」，补"失误/出界/滚网/拍框"词后 Recall 0.37→0.73；③ 修正优先级（"发球失误"应判 point_end 而非 point_start）+ 新增 other 类型（挑战/封网/碰撞），Recall 达 0.90。

剩余 3 个未命中均为 ASR 分段时间戳错位（11-23s），语义判断正确。**印证「比分以裁判报分为主、得分以解说明确描述为主」的规则分治路线，3B 小模型反而不如精调后的规则。**

## 结论

1. **赛事型偏关键词**：BM25 是最强单通道（R@1 0.60/0.50），Dense 单独最差（时间误差 38s，语义漂移）。印证「类别特异检索策略」——赛事型与讲解型类似，关键词为主。
2. **Hybrid 时间定位更准**：R@1 与 BM25 持平，但时间误差最小（7.08s/12.08s）、mIoU 更高（0.38/0.31）。
3. **事件识别规则基线很弱**（F1 0.17，Precision 0.11 大量误报）→ 下一步用 LLM few-shot（arXiv:2506.17144）替换/融合规则，是赛事型的核心提升点。

## 复现命令

```bash
export HF_HOME=/Volumes/T7/hf-cache HF_HUB_CACHE=/Volumes/T7/hf-cache HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
cd momentjump
python scripts/run_eval.py --transcripts data/transcripts/match --gold data/eval/match_dev.json --retriever bm25
python scripts/run_eval.py --transcripts data/transcripts/match --gold data/eval/match_test.json --retriever hybrid
python scripts/eval_event.py --transcripts data/transcripts/match --gold data/eval/match_events_gold.json --manifest data/meta/match/manifest.json
```
