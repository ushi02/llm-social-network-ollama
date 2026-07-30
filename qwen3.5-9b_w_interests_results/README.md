# qwen3.5:9b 实验结果（2026-07-30）

在 DGX Ollama 服务（`http://10.236.129.210:11434`）上，用 `qwen3.5:9b` 跑了一次 `sequential` + `w_interests`（原论文标准设置），personas 用仓库自带的 `text-files/us_50_gpt4o_w_interests.json`（50人），n=3（seed 0/1/2），和之前 `gemma4:e4b`/`mistral-small3.2:24b` 的对比样本量一致。

## 关键修复：关闭 reasoning

`qwen3.5:9b` 是带思考链的模型。之前（2026-07-24 会话，见 `PROGRESS_ja.md`）曾因为默认开启 reasoning 导致单次真实 prompt 调用耗时 **529.9 秒**，150 次调用（50人×3网络）预计要 22 小时，实验被迫中止。

这次确认：Ollama 的 **OpenAI 兼容接口**（`/v1/chat/completions`）传 `"think": false` **不完全生效**（reasoning 仍会输出，只是长度不稳定地变短）。改用 Ollama **原生接口**（`/api/chat`）传 `"think": false` 才会**完全关闭**思考过程。

已将 `constants_and_utils.py` 里 `get_llm_response()` 的 Ollama 分支从走 OpenAI 兼容客户端改成直接调用原生 `/api/chat`（默认 `think=False`）。实测同样规模的真实 prompt（system 810字符 + user 8326字符）耗时从 529.9 秒降到 **约3.1秒**，提速约170倍。本次实验 3 个网络全部顺利跑完，总耗时约 6.5 分钟，50/50 次调用全部一次成功解析（`num_tries=50`，无重试）。

## 结果对比：qwen3.5:9b（n=3） vs GPT-3.5（n=30，原论文自带数据 `stats/sequential_gpt-3.5-turbo_w_interests`）

### 结构性指标（均值，括号内为标准差）

| 指标 | qwen3.5:9b (n=3) | GPT-3.5 (n=30，原论文) |
|---|---|---|
| density | 0.387 (0.029) | 0.140 (0.012) |
| avg_clustering_coef | 0.829 (0.054) | 0.456 (0.057) |
| modularity | 0.446 (0.036) | 0.412 (0.035) |
| avg_shortest_path（正规化） | 0.466 (0.096) | 0.591 (0.029) |

qwen3.5:9b 生成的网络密度远高于 GPT-3.5——平均边数分别为 502/434/485，而 GPT-3.5 平均约171条边。原因是 qwen3.5:9b 每次经常一口气选择十几到二十个朋友（如某次回复 `4,8,10,11,13,...`，一次性选了20人），比 GPT-3.5 更倾向于"广撒网"。

### 同质性（homophily）：same_ratio（1.0 = 随机基线）

| 属性 | qwen3.5:9b | GPT-3.5 |
|---|---|---|
| age | 1.230 (0.022) | 1.548 (0.160) |
| gender | 1.049 (0.003) | 1.318 (0.088) |
| race/ethnicity | 1.007 (0.017) | 1.150 (0.100) |
| religion | 1.044 (0.028) | 1.259 (0.115) |
| **political affiliation** | **1.919 (0.089)** | **1.725 (0.095)** |

### 同质性：cross_ratio（越低越"抱团"/隔离）

| 属性 | qwen3.5:9b | GPT-3.5 |
|---|---|---|
| age | 0.820 (0.007) | 0.751 (0.062) |
| gender | 0.953 (0.003) | 0.694 (0.085) |
| race/ethnicity | 0.994 (0.015) | 0.865 (0.090) |
| religion | 0.977 (0.014) | 0.867 (0.059) |
| **political affiliation** | **0.115 (0.086)** | **0.302 (0.092)** |

## 结论

- **核心发现被复现**：political affiliation 是唯一一个 qwen3.5:9b 明显比 GPT-3.5 更极端的维度——cross_ratio 只有 GPT-3.5 的约 1/3，即网络里的人几乎只跟同党派的人做朋友。其余四个维度（age/gender/race/religion）上，qwen3.5:9b 反而比 GPT-3.5 更接近随机基线（same_ratio 更接近1.0）。
- 这与之前 `gemma4:e4b` 的结果（political affiliation cross_ratio 低至 0.023，见 `PROGRESS_ja.md`）方向一致，但幅度更温和（qwen3.5:9b 是 0.115，gemma4:e4b 是 0.023）——说明"开源模型放大政治同质性偏差"这个现象不是 gemma4 系列独有的，但不同模型放大的程度不同。
- **注意**：样本量仅 n=3，且 qwen3.5:9b 的网络明显比 GPT-3.5 更密（更多边），这可能会影响同质性指标的可比性，结论置信度有限，建议后续增加 seed 数量。

## 文件说明

- `networks/qwen3.5:9b_w_interests_{0,1,2}.adj`：生成的网络邻接表
- `plots/qwen3.5:9b_w_interests_{0,1,2}.png`：网络可视化
- `stats/network_metrics.csv`、`stats/homophily.csv`：结构指标与同质性原始数据（每个网络、每个属性一行）
- `stats/cost_stats_s0-2.csv`：生成耗时与 token 用量

这些文件此前在旧路径下（`text-files/sequential_ollama/`、`plots/sequential_ollama/`、`stats/sequential_ollama/qwen3.5:9b_w_interests/`）也有一份未提交的重复副本，本文件夹整理完成后已删除那些重复副本——这里是唯一保留的一份。
