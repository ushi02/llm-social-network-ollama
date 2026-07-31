# gemma4:e4b（w_interests）实验结果（2026-07-17）

在 DGX Ollama 服务上，用 `gemma4:e4b` 跑了 `sequential` + `w_interests`（原论文标准设置），persona 用仓库自带的 `text-files/us_50_gpt4o_w_interests.json`（50人），n=3（seed 0/1/2），命令：

```
generate_networks.py sequential --model ollama/gemma4:e4b --persona_fn us_50_gpt4o_w_interests.json --include_interests --num_networks 1
```
(分三次跑，seed 0/1/2 各一次)

对比对象：原论文 GPT-3.5 `w_interests` 结果（`stats/sequential_gpt-3.5-turbo_w_interests`，n=30）。

## 结果对比：gemma4:e4b（n=3） vs GPT-3.5（n=30，原论文自带数据）

### 结构性指标（均值，括号内为标准差）

| 指标 | gemma4:e4b (n=3) | GPT-3.5 (n=30，原论文) |
|---|---|---|
| density | 0.235 (0.017) | 0.140 (0.012) |
| avg_clustering_coef | 0.692 (0.059) | 0.456 (0.057) |
| modularity | 0.490 (0.018) | 0.412 (0.035) |
| avg_shortest_path（正规化） | 0.706 (0.069) | 0.591 (0.029) |

gemma4:e4b 生成的网络比 GPT-3.5 更密、聚类系数更高，网络整体更"抱团"。

### 同质性（homophily）：same_ratio（1.0 = 随机基线）

| 属性 | gemma4:e4b | GPT-3.5 |
|---|---|---|
| age | 1.572 (0.052) | 1.548 (0.160) |
| gender | 1.178 (0.070) | 1.318 (0.088) |
| race/ethnicity | 1.091 (0.070) | 1.150 (0.100) |
| religion | 1.315 (0.103) | 1.259 (0.115) |
| **political affiliation** | **2.015 (0.010)** | **1.725 (0.095)** |

### 同质性：cross_ratio（越低越"抱团"/隔离）

| 属性 | gemma4:e4b | GPT-3.5 |
|---|---|---|
| age | 0.683 (0.026) | 0.751 (0.062) |
| gender | 0.829 (0.067) | 0.694 (0.085) |
| race/ethnicity | 0.918 (0.063) | 0.865 (0.090) |
| religion | 0.838 (0.053) | 0.867 (0.059) |
| **political affiliation** | **0.023 (0.010)** | **0.302 (0.092)** |

## 生成成本

3 个网络全部 50/50 次调用一次成功解析（`num_tries=50`，无重试）。单个网络耗时约 2,162~2,279 秒（36~38 分钟），输入约 58,738 tokens/次（因为带 interests 描述，prompt 明显更长）。

## 结论

- **核心发现被复现且被放大**：political affiliation 是唯一一个 gemma4:e4b 明显比 GPT-3.5 更极端的维度——cross_ratio 只有 GPT-3.5 的约 1/13，网络里的人几乎只跟同党派的人做朋友。其余四个维度上 gemma4:e4b 和 GPT-3.5 相差不大，互有高低。
- 这是把仓库里已有的 `gemma4:e4b_w_interests` 实验结果按标准格式重新汇总，原始分析记录见 `PROGRESS.md`（2026-07-17）。
- **注意**：样本量仅 n=3，且 gemma4:e4b 的网络明显比 GPT-3.5 更密（更多边），这可能会影响同质性指标的可比性，结论置信度有限。

## 文件说明

- `networks/gemma4:e4b_w_interests_{0,1,2}.adj`：生成的网络邻接表
- `plots/gemma4:e4b_w_interests_{0,1,2}.png`：网络可视化
- `stats/network_metrics.csv`、`stats/homophily.csv`：结构指标与同质性原始数据
- `stats/cost_stats_s0-0.csv`、`stats/cost_stats_s1-2.csv`：生成耗时与 token 用量（分两批跑，故拆成两个文件）

原始文件也仍保留在仓库常规路径下（`text-files/sequential_ollama/`、`plots/sequential_ollama/`、`stats/sequential_ollama_gemma4-e4b_w_interests/`），本文件夹是汇总副本，方便单独查看这次实验的结果。
