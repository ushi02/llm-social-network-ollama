# qwen3.5:9b 实验结果（2026-07-30，2026-08-05 扩充至 n=10）

在 DGX Ollama 服务（`http://10.236.129.210:11434`）上，用 `qwen3.5:9b` 跑了 `sequential` + `w_interests`（原论文标准设置），personas 用仓库自带的 `text-files/us_50_gpt4o_w_interests.json`（50人）。seed 0/1/2 于 2026-07-30 生成，seed 3-9 于 2026-08-05 补跑（`--num_networks 7 --start_seed 3`），把样本量从 n=3 扩充到 n=10。

## 关键修复：关闭 reasoning

`qwen3.5:9b` 是带思考链的模型。之前（2026-07-24 会话，见 `PROGRESS_ja.md`）曾因为默认开启 reasoning 导致单次真实 prompt 调用耗时 **529.9 秒**，150 次调用（50人×3网络）预计要 22 小时，实验被迫中止。

这次确认：Ollama 的 **OpenAI 兼容接口**（`/v1/chat/completions`）传 `"think": false` **不完全生效**（reasoning 仍会输出，只是长度不稳定地变短）。改用 Ollama **原生接口**（`/api/chat`）传 `"think": false` 才会**完全关闭**思考过程。

已将 `constants_and_utils.py` 里 `get_llm_response()` 的 Ollama 分支从走 OpenAI 兼容客户端改成直接调用原生 `/api/chat`（默认 `think=False`）。实测同样规模的真实 prompt（system 810字符 + user 8326字符）耗时从 529.9 秒降到 **约3.1秒**，提速约170倍。

## 结果对比：qwen3.5:9b（n=10） vs GPT-3.5（n=30，原论文自带数据 `stats/sequential_gpt-3.5-turbo_w_interests`）

### 结构性指标（均值，括号内为标准差）

| 指标 | qwen3.5:9b (n=10) | GPT-3.5 (n=30，原论文) |
|---|---|---|
| density | 0.373 (0.035) | 0.140 (0.012) |
| avg_clustering_coef | 0.817 (0.032) | 0.456 (0.057) |
| modularity | 0.453 (0.030) | 0.412 (0.035) |
| avg_shortest_path（正规化） | 0.482 (0.064) | 0.591 (0.029) |

qwen3.5:9b 生成的网络密度依然远高于 GPT-3.5，n=10 后的估计（0.373）比 n=3 时（0.387）略低但同一量级，结论不变：qwen3.5:9b 比 GPT-3.5 更倾向于"广撒网"交朋友。

### 同质性（homophily）：same_ratio（1.0 = 随机基线）

| 属性 | qwen3.5:9b (n=10) | GPT-3.5 |
|---|---|---|
| age | 1.261 (0.059) | 1.548 (0.160) |
| gender | 1.036 (0.016) | 1.318 (0.088) |
| race/ethnicity | 0.990 (0.027) | 1.150 (0.100) |
| religion | 1.048 (0.023) | 1.259 (0.115) |
| **political affiliation** | **1.943 (0.065)** | **1.725 (0.095)** |

### 同质性：cross_ratio（越低越"抱团"/隔离）

| 属性 | qwen3.5:9b (n=10) | GPT-3.5 |
|---|---|---|
| age | 0.813 (0.036) | 0.751 (0.062) |
| gender | 0.965 (0.015) | 0.694 (0.085) |
| race/ethnicity | 1.009 (0.024) | 0.865 (0.090) |
| religion | 0.975 (0.012) | 0.867 (0.059) |
| **political affiliation** | **0.092 (0.063)** | **0.302 (0.092)** |

## 生成成本

- seed 0-2：50/50 次调用一次成功解析，总耗时约 6.5 分钟。
- seed 3-9：同样 50/50 一次成功，单个网络约 110~130 秒，7 个网络合计约 14.4 分钟，与之前的耗时量级一致（DGX 这次同样不忙）。

## 结论

- **核心发现在 n=10 下依然成立且更稳健**：political affiliation 是唯一一个 qwen3.5:9b 明显比 GPT-3.5 更极端的维度——cross_ratio (0.092) 只有 GPT-3.5 (0.302) 的约 1/3，即网络里的人几乎只跟同党派的人做朋友。标准差（0.063）比 n=3 时（0.070，样本更小反而不稳）略有下降，估计更可信。其余四个维度（age/gender/race/religion）上，qwen3.5:9b 反而比 GPT-3.5 更接近随机基线（same_ratio 更接近1.0），n=3→n=10 后数值基本没变（如 political same_ratio 1.919→1.943），说明这不是抽样偶然。
- 这与 `gemma4:e4b`（n=10 后 political cross_ratio 为 0.068，见 `../gemma4-e4b_w_interests_results/README.md`）和 `qwen3.5:27b`（0.048，见 `../qwen3.5-27b_w_interests_results/README.md`）方向一致——"开源模型放大政治同质性偏差"这个现象不是某一个模型独有的，但不同模型放大的程度不同，且模型变大（9b→27b）并没有缓解这个偏差，反而更极端。
- **注意**：qwen3.5:9b 的网络明显比 GPT-3.5 更密（更多边），这可能会持续影响同质性指标的可比性；样本量已从 n=3 提升到 n=10，若要进一步对齐 GPT-3.5 的 n=30，仍可以考虑继续补 seed。

## 文件说明

- `networks/qwen3.5:9b_w_interests_{0..9}.adj`：生成的网络邻接表
- `plots/qwen3.5:9b_w_interests_{0..9}.png`：网络可视化
- `stats/network_metrics.csv`、`stats/homophily.csv`：结构指标与同质性原始数据（已更新为 n=10 全量重算）
- `stats/cost_stats_s0-2.csv`、`stats/cost_stats_s3-9.csv`：生成耗时与 token 用量（分两批跑，故拆成两个文件）

这个模型没有保留单独的 raw 镜像副本（此前的旧路径重复副本已清理）——本文件夹是唯一保留的一份。
