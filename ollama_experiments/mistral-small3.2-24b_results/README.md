# mistral-small3.2:24b 实验结果（2026-07-23）

在 DGX Ollama 服务上，用 `mistral-small3.2:24b` 跑了 `sequential`（bare 条件，不带 interests，英文 prompt），50 人标准 persona 集，n=3（seed 0/1/2），命令：

```
generate_networks.py sequential --model ollama/mistral-small3.2:24b --num_networks 3
```

对比对象：原论文 GPT-3.5 bare 结果（`stats/sequential_gpt-3.5-turbo`，n=30），条件与 [[gemma4-e4b_lang_results]] 里的 `en` 组一致，可横向对比。

## 结果对比：mistral-small3.2:24b（n=3） vs GPT-3.5（n=30，原论文自带数据）

### 结构性指标（均值，括号内为标准差）

| 指标 | mistral-small3.2:24b (n=3) | GPT-3.5 bare (n=30，原论文) |
|---|---|---|
| density | 0.377 (0.014) | 0.149 (0.013) |
| avg_clustering_coef | 0.813 (0.040) | 0.495 (0.069) |
| modularity | 0.483 (0.013) | 0.365 (0.051) |
| avg_shortest_path（正规化） | 0.472 (0.106) | 0.561 (0.028) |

mistral 生成的网络密度是 GPT-3.5 的两倍多，聚类系数也明显更高——同样表现出比 GPT-3.5 更"抱团"的倾向。

### 同质性（homophily）：same_ratio（1.0 = 随机基线）

| 属性 | mistral-small3.2:24b | GPT-3.5 |
|---|---|---|
| age | 1.142 (0.041) | 1.258 (0.154) |
| gender | 1.091 (0.025) | 1.230 (0.100) |
| race/ethnicity | 1.050 (0.018) | 1.218 (0.110) |
| religion | 1.135 (0.080) | 1.370 (0.169) |
| **political affiliation** | **2.021 (0.027)** | **1.685 (0.129)** |

### 同质性：cross_ratio（越低越"抱团"/隔离）

| 属性 | mistral-small3.2:24b | GPT-3.5 |
|---|---|---|
| age | 0.888 (0.016) | 0.900 (0.073) |
| gender | 0.912 (0.024) | 0.779 (0.096) |
| race/ethnicity | 0.955 (0.017) | 0.804 (0.099) |
| religion | 0.931 (0.041) | 0.810 (0.087) |
| **political affiliation** | **0.017 (0.026)** | **0.340 (0.125)** |

## 生成成本

3 个网络中有 cost 记录的两个(seed 1/2)均 50/50 次调用一次成功解析,单网络耗时差异较大(seed 1 约 4,720 秒 ≈ 79 分钟, seed 2 约 1,482 秒 ≈ 25 分钟),可能与 DGX 共享资源的实时负载有关。

## 结论

- **核心发现被复现**:political affiliation 的 cross_ratio(0.017)远低于其他四个维度(0.89~0.96),且远低于 GPT-3.5 的 0.34——网络里的人几乎只跟同党派的人做朋友,其他维度上的同质性反而比 GPT-3.5 更接近随机基线。
- 和同一条件(bare, 英文)下的 `gemma4:e4b`(见 [[gemma4-e4b_lang_results]] 的 en 组,density 0.143)相比,mistral-small3.2:24b 的网络密度(0.377)明显更高,说明"政治同质性被放大"这个现象在不同开源模型间一致,但网络整体密度/抱团程度因模型而异。
- **注意**:样本量仅 n=3,且只有 2 个种子留有完整 cost 记录,置信度有限,建议后续增加种子数。

## 文件说明

- `networks/mistral-small3.2:24b_{0,1,2}.adj`:生成的网络邻接表
- `plots/mistral-small3.2:24b_{0,1,2}.png`:网络可视化
- `plots/edge_distance.png`、`plots/edge_props.png`、`plots/num_edges.png`:跨 3 个网络的汇总图(边长分布/边属性/边数)
- `stats/network_metrics.csv`、`stats/homophily.csv`:结构指标与同质性原始数据(每个网络、每个属性一行)
- `stats/cost_stats_s1-2.csv`:生成耗时与 token 用量(仅 seed 1/2 有记录)

原始的每网络文件(`.adj`/`.png`)和 `cost_stats_s1-2.csv` 仍保留在仓库常规路径下(`text-files/sequential_ollama/mistral-small3.2:24b_*`、`plots/sequential_ollama/mistral-small3.2:24b_*`、`stats/sequential_ollama/mistral-small3.2:24b/`,这些是已提交的原始产物);本文件夹是汇总副本,方便单独查看这次实验的结果。汇总图(`edge_distance.png` 等 3 张)和 `network_metrics.csv`/`homophily.csv` 此前在旧路径下是未提交的重复文件,已合并到这里,旧路径的重复副本已清理。
