# gemma4:e4b（w_interests）实验结果（2026-07-17，2026-08-05 扩充至 n=10）

在 DGX Ollama 服务上，用 `gemma4:e4b` 跑了 `sequential` + `w_interests`（原论文标准设置），persona 用仓库自带的 `text-files/us_50_gpt4o_w_interests.json`（50人）。

- seed 0/1/2：2026-07-17 跑的，命令：
  ```
  generate_networks.py sequential --model ollama/gemma4:e4b --persona_fn us_50_gpt4o_w_interests.json --include_interests --num_networks 1
  ```
  （分三次跑，seed 0/1/2 各一次）
- seed 3-9：2026-08-05 补跑，把样本量从 n=3 扩充到 n=10，命令：
  ```
  generate_networks.py sequential --model ollama/gemma4:e4b --persona_fn us_50_gpt4o_w_interests.json --include_interests --num_networks 7 --start_seed 3
  ```

对比对象：原论文 GPT-3.5 `w_interests` 结果（`stats/sequential_gpt-3.5-turbo_w_interests`，n=30）。

## 结果对比：gemma4:e4b（n=10） vs GPT-3.5（n=30，原论文自带数据）

### 结构性指标（均值，括号内为标准差）

| 指标 | gemma4:e4b (n=10) | GPT-3.5 (n=30，原论文) |
|---|---|---|
| density | 0.260 (0.024) | 0.140 (0.012) |
| avg_clustering_coef | 0.696 (0.041) | 0.456 (0.057) |
| modularity | 0.464 (0.030) | 0.412 (0.035) |
| avg_shortest_path（正规化） | 0.622 (0.086) | 0.591 (0.029) |

gemma4:e4b 生成的网络比 GPT-3.5 更密、聚类系数更高，网络整体更"抱团"。n=10 下 density/avg_clustering_coef 略低于 n=3 时的估计（0.235→0.260 其实略升，0.692→0.696 基本持平），结论方向不变。

### 同质性（homophily）：same_ratio（1.0 = 随机基线）

| 属性 | gemma4:e4b (n=10) | GPT-3.5 |
|---|---|---|
| age | 1.449 (0.096) | 1.548 (0.160) |
| gender | 1.215 (0.052) | 1.318 (0.088) |
| race/ethnicity | 1.075 (0.045) | 1.150 (0.100) |
| religion | 1.189 (0.109) | 1.259 (0.115) |
| **political affiliation** | **1.968 (0.060)** | **1.725 (0.095)** |

### 同质性：cross_ratio（越低越"抱团"/隔离）

| 属性 | gemma4:e4b (n=10) | GPT-3.5 |
|---|---|---|
| age | 0.725 (0.035) | 0.751 (0.062) |
| gender | 0.793 (0.051) | 0.694 (0.085) |
| race/ethnicity | 0.932 (0.040) | 0.865 (0.090) |
| religion | 0.903 (0.056) | 0.867 (0.059) |
| **political affiliation** | **0.068 (0.058)** | **0.302 (0.092)** |

## 生成成本

- seed 0-2（2026-07-17）：50/50 次调用一次成功解析，单个网络耗时约 2,162~2,279 秒（36~38 分钟）。
- seed 3-9（2026-08-05）：同样 50/50 一次成功，但这次 DGX 空闲，单个网络只耗时约 59~70 秒——差了约 30 倍，说明这个模型本身调用不慢，之前的耗时主要是共享 DGX 资源被占用导致的排队/竞争。跑之前建议照常 spot-check 一下延迟，不要直接套用旧的耗时估计。
- 两批合计输入约 58,738 tokens/次（因为带 interests 描述，prompt 明显更长）。

## 结论

- **核心发现被复现且被放大，且随样本量增加更稳健**：political affiliation 仍是唯一一个 gemma4:e4b 明显比 GPT-3.5 更极端的维度——cross_ratio (0.068) 只有 GPT-3.5 (0.302) 的约 1/4 到 1/13 之间（n=3 时曾低至 0.023，n=10 后回升到 0.068，说明 n=3 时那个极端值有一部分是抽样偶然性，但即使用更大的样本，political affiliation 的隔离程度依然远超其他四个维度、也远超 GPT-3.5）。
- 其余四个维度上 gemma4:e4b 和 GPT-3.5 相差不大，互有高低，且 n=10 后的数值比 n=3 时更接近 GPT-3.5（比如 age same_ratio 从 1.572 降到 1.449，更接近 GPT-3.5 的 1.548）——反映出小样本（n=3）时这些非政治维度的估计噪声较大。
- **注意**：即使 n=10，gemma4:e4b 的网络仍明显比 GPT-3.5 更密（更多边），这可能会持续影响同质性指标的可比性；若要进一步缩小置信区间，可以考虑追加到 n=30 与 GPT-3.5 对齐。

## 文件说明

- `networks/gemma4:e4b_w_interests_{0..9}.adj`：生成的网络邻接表
- `plots/gemma4:e4b_w_interests_{0..9}.png`：网络可视化
- `stats/network_metrics.csv`、`stats/homophily.csv`：结构指标与同质性原始数据（已更新为 n=10 全量重算）
- `stats/cost_stats_s0-0.csv`、`stats/cost_stats_s1-2.csv`、`stats/cost_stats_s3-9.csv`：生成耗时与 token 用量（分三批跑，故拆成三个文件）

原始文件也在 `ollama_experiments/raw/text-files/sequential_ollama/`、`ollama_experiments/raw/plots/sequential_ollama/`、`ollama_experiments/raw/stats/sequential_ollama/gemma4:e4b_w_interests/` 下保留一份镜像副本，本文件夹是整理过的汇总版本。
