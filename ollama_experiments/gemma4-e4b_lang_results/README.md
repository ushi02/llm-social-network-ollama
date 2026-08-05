# gemma4:e4b 多语言实验结果（en / zh / ja，2026-07-23，2026-08-05 扩充至 n=10）

在 DGX Ollama 服务上，用 `gemma4:e4b` 跑了 `sequential`（bare 条件，不带 interests），50 人标准 persona 集，分别用英文、中文、日文 prompt 生成网络。

- seed 0/1/2：2026-07-23 跑的，命令：
  ```
  generate_networks.py sequential --model ollama/gemma4:e4b --num_networks 3            # en
  generate_networks.py sequential --model ollama/gemma4:e4b --lang zh --num_networks 3   # zh
  generate_networks.py sequential --model ollama/gemma4:e4b --lang ja --num_networks 3   # ja
  ```
- seed 3-9：2026-08-05 补跑，把三种语言的样本量都从 n=3 扩充到 n=10，命令：
  ```
  generate_networks.py sequential --model ollama/gemma4:e4b --start_seed 3 --num_networks 7            # en
  generate_networks.py sequential --model ollama/gemma4:e4b --lang zh --start_seed 3 --num_networks 7   # zh
  generate_networks.py sequential --model ollama/gemma4:e4b --lang ja --start_seed 3 --num_networks 7   # ja
  ```

目的：看 prompt 语言本身是否会影响生成网络的结构和同质性（尤其是政治立场同质性）。

## 结构性指标（均值，括号内为标准差，各 n=10）

| 指标 | en | zh | ja |
|---|---|---|---|
| density | 0.301 (0.112) | 0.243 (0.089) | 0.194 (0.067) |
| avg_clustering_coef | 0.724 (0.135) | 0.678 (0.090) | 0.621 (0.123) |
| modularity | 0.489 (0.018) | 0.511 (0.061) | 0.513 (0.071) |
| avg_shortest_path（正规化） | 0.613 (0.173) | 0.692 (0.156) | 0.731 (0.257) |

英文网络密度仍然最高，日文最低——n=10 后的顺序（en > zh > ja）和 n=3 时一致，但方差明显变大了（尤其 density 和 avg_shortest_path），说明 n=3 时的估计比看起来更不稳定。

## 同质性（homophily）：same_ratio（1.0 = 随机基线）

| 属性 | en | zh | ja |
|---|---|---|---|
| age | 1.239 (0.247) | 1.299 (0.211) | 1.376 (0.269) |
| gender | 1.247 (0.169) | 1.402 (0.251) | 1.431 (0.220) |
| race/ethnicity | 1.241 (0.189) | 1.384 (0.178) | 1.457 (0.180) |
| religion | 1.351 (0.355) | 1.393 (0.283) | 1.399 (0.304) |
| **political affiliation** | **2.008 (0.043)** | **2.013 (0.022)** | **2.011 (0.024)** |

## 同质性：cross_ratio（越低越"抱团"/隔离）

| 属性 | en | zh | ja |
|---|---|---|---|
| age | 0.872 (0.089) | 0.835 (0.066) | 0.779 (0.073) |
| gender | 0.762 (0.162) | 0.613 (0.242) | 0.585 (0.212) |
| race/ethnicity | 0.783 (0.170) | 0.655 (0.160) | 0.589 (0.162) |
| religion | 0.819 (0.183) | 0.798 (0.146) | 0.795 (0.156) |
| **political affiliation** | **0.029 (0.041)** | **0.025 (0.021)** | **0.026 (0.023)** |

三种语言下 political affiliation 的 same_ratio（2.008~2.013）和 cross_ratio（0.025~0.029）在 n=10 后依然几乎完全一致，且这是五个维度里跨语言方差最小的——n=3 时的结论被 n=10 进一步坐实：**这个偏差与 prompt 语言无关，是模型本身的特性**。

其余四个维度（age/gender/race/religion）在 n=10 下反而比 n=3 时显示出更明显的跨语言差异，尤其 gender 和 race/ethnicity 的 cross_ratio 从 en 到 ja 呈现下降趋势（模型在中日文 prompt 下对性别、种族的隔离更强），这一点在 n=3 时因样本太小没能看出来。

## 生成成本

- seed 0-2（2026-07-23）：zh/ja 各 50/50 次调用一次成功解析，单网络耗时约 1,695~1,777 秒（28~30 分钟）；en 的耗时记录来自更早的一批调用，未保留完整 cost 数据。
- seed 3-9（2026-08-05）：三种语言全部 50/50 一次成功，但这次 DGX 明显空闲，单网络耗时骤降到约 46~69 秒——比 seed 0-2 快了约 25~35 倍，与 `gemma4:e4b_w_interests` 那次补跑观察到的现象一致：耗时主要取决于 DGX 是否被抢占，不是模型本身慢。

## 结论

- **political affiliation 同质性偏差与 prompt 语言无关，n=10 后进一步确认**：无论用英文、中文还是日文提问，same_ratio 都稳定在约 2.0、cross_ratio 都在 0.02~0.03，是五个维度里跨语言最一致的一个，且方差远小于其他维度。
- 网络密度呈 en > zh > ja 的顺序，日文条件下模型更"惜友"，倾向选更少的朋友，网络也因此更分散（modularity 更高、平均最短路径更长）——n=10 后该顺序保持不变，但置信区间比 n=3 时看起来要宽。
- **新发现（n=3 时样本太小看不出来）**：gender、race/ethnicity 的 cross_ratio 随语言从 en→zh→ja 递减，暗示中日文 prompt 下模型对性别/种族的隔离倾向可能比英文更强；这个趋势值得在更大样本下（如 n=30）进一步验证。
- 关于社区结构（louvain 社区数/大小）和友谊数不平等度（标准差/基尼系数）等更细的分析，详见 `PROGRESS_ja.md`（2026-07-24 会话记录，仍是 n=3 时的分析，尚未随 n=10 更新），本 README 只汇总了核心结构与同质性指标。

## 文件说明

- `networks/{en,zh,ja}/`：各语言生成的网络邻接表（`.adj`，`gemma4:e4b{,_zh,_ja}_{0..9}.adj`）
- `plots/{en,zh,ja}/`：各语言的网络可视化
- `stats/{en,zh,ja}/network_metrics.csv`、`homophily.csv`：结构指标与同质性原始数据（已更新为 n=10 全量重算）
- `stats/{en,zh,ja}/cost_stats_s1-2.csv`、`cost_stats_s3-9.csv`：生成耗时与 token 用量（分两批跑，故拆成两个文件；en 没有 seed 0 的 cost 记录）

原始文件也仍保留在仓库常规路径下（`text-files/sequential_ollama/gemma4:e4b{,_zh,_ja}_*`、`plots/sequential_ollama/gemma4:e4b{,_zh,_ja}*`、`stats/sequential_ollama/gemma4:e4b{,_zh,_ja}/`，均为未跟踪的本地文件），以及 `ollama_experiments/raw/` 下的镜像副本；本文件夹是整理过的汇总版本。
