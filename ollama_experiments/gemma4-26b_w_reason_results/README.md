# gemma4:26b（w_reason）实验结果（2026-04-23）

在 DGX Ollama 服务上，用 `gemma4:26b` 跑了 `sequential` + `--include_reason`（要求模型在选择朋友时输出理由），persona 用仓库自带的 50 人标准集，n=10（seed 0-9），命令：

```
generate_networks.py sequential --model ollama/gemma4:26b --num_networks 10 --include_reason --verbose
```

对比对象：原论文 GPT-3.5 `w_reason` 结果（`stats/sequential_gpt-3.5-turbo_w_reason`，同为 n=10）。

## 结果对比：gemma4:26b（n=10） vs GPT-3.5（n=10，原论文自带数据）

### 结构性指标（均值，括号内为标准差）

| 指标 | gemma4:26b (n=10) | GPT-3.5 (n=10，原论文) |
|---|---|---|
| density | 0.453 (0.014) | 0.136 (0.012) |
| avg_clustering_coef | 0.931 (0.010) | 0.476 (0.060) |
| modularity | 0.493 (0.004) | 0.364 (0.054) |
| avg_shortest_path（正规化） | 0.528 (0.048) | 0.579 (0.035) |

gemma4:26b 生成的网络密度是 GPT-3.5 的三倍多，聚类系数也高得多（0.93 vs 0.48）——模型几乎把每个人的朋友圈都变成了高度抱团的小团体。

### 同质性（homophily）：same_ratio（1.0 = 随机基线）

| 属性 | gemma4:26b | GPT-3.5 |
|---|---|---|
| age | 1.085 (0.023) | 1.206 (0.106) |
| gender | 0.998 (0.011) | 1.226 (0.087) |
| race/ethnicity | 1.020 (0.013) | 1.291 (0.110) |
| religion | 1.031 (0.016) | 1.340 (0.099) |
| **political affiliation** | **2.026 (0.008)** | **1.724 (0.124)** |

### 同质性：cross_ratio（越低越"抱团"/隔离）

| 属性 | gemma4:26b | GPT-3.5 |
|---|---|---|
| age | 0.927 (0.015) | 0.917 (0.063) |
| gender | 1.002 (0.010) | 0.782 (0.083) |
| race/ethnicity | 0.982 (0.012) | 0.738 (0.099) |
| religion | 0.984 (0.008) | 0.825 (0.051) |
| **political affiliation** | **0.012 (0.007)** | **0.302 (0.119)** |

## 生成成本

10 个网络全部 50/50 次调用一次成功解析（`num_tries=50`，无重试）。单个网络平均耗时约 731 秒（12 分钟），10 个网络总计约 2 小时；输入约 30,838 tokens/次，输出约 6,522 tokens/次（因为要求模型额外输出理由，输出量明显高于不带 reason 的条件）。

## 结论

- **核心发现被复现**：political affiliation 同样是唯一一个 gemma4:26b 明显比 GPT-3.5 更极端的维度——cross_ratio 只有 GPT-3.5 的约 1/25,几乎是"只跟同党派的人做朋友"。
- 与其他四个维度（age/gender/race/religion）相比，gemma4:26b 在这些维度上的 same_ratio 反而**更接近随机基线**（更接近1.0),说明政治立场的同质性偏差是独立、专属的现象,不是整体网络更"抱团"带来的副作用。
- 但要注意:gemma4:26b 整体网络密度和聚类系数远高于 GPT-3.5(见结构性指标表),网络本身就比 GPT-3.5 更"抱团",这可能会放大所有同质性指标(包括 cross_ratio 更低),需要结合密度差异一起解读,不能单独看同质性数字。
- 这是"要求模型输出选择理由"(w_reason)条件下的实验,和其他几个 `_results` 文件夹里的 `w_interests`/bare 条件不是同一套设置,横向比较时需注意。

## 文件说明

- `networks/gemma4:26b_w_reason_{0..9}.adj`:生成的网络邻接表
- `networks/gemma4:26b_w_reason_{0..9}_reasons.json`:模型给出的朋友选择理由
- `plots/gemma4:26b_w_reason_{0..9}.png`:网络可视化
- `plots/gemma4:26b_w_reason_0_politics.png`:seed 0 网络按政党着色的可视化
- `stats/network_metrics.csv`、`stats/homophily.csv`:结构指标与同质性原始数据
- `stats/cost_stats_s0-9.csv`:生成耗时与 token 用量

原始文件也仍保留在仓库常规路径下(`plots/sequential_ollama/gemma4:26b_w_reason/`、`stats/sequential_ollama/gemma4:26b_w_reason/`),本文件夹是汇总副本,方便单独查看这次实验的结果。
