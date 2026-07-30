# gemma4:e4b 多语言实验结果（en / zh / ja，2026-07-23）

在 DGX Ollama 服务上，用 `gemma4:e4b` 跑了 `sequential`（bare 条件，不带 interests），50 人标准 persona 集，分别用英文、中文、日文 prompt 各生成 n=3（seed 0/1/2），命令：

```
generate_networks.py sequential --model ollama/gemma4:e4b --num_networks 3            # en
generate_networks.py sequential --model ollama/gemma4:e4b --lang zh --num_networks 3   # zh
generate_networks.py sequential --model ollama/gemma4:e4b --lang ja --num_networks 3   # ja
```

目的：看 prompt 语言本身是否会影响生成网络的结构和同质性（尤其是政治立场同质性）。

## 结构性指标（均值，括号内为标准差，各 n=3）

| 指标 | en | zh | ja |
|---|---|---|---|
| density | 0.143 (0.015) | 0.118 (0.017) | 0.102 (0.005) |
| avg_clustering_coef | 0.540 (0.032) | 0.550 (0.006) | 0.448 (0.048) |
| modularity | 0.501 (0.009) | 0.559 (0.081) | 0.597 (0.024) |
| avg_shortest_path（正规化） | 0.829 (0.139) | 0.902 (0.046) | 1.079 (0.019) |

英文网络密度最高，日文最低——日文条件下模型倾向于给每个人选更少的朋友。

## 同质性（homophily）：political affiliation

| 指标 | en | zh | ja |
|---|---|---|---|
| same_ratio（1.0=随机基线） | 1.999 (0.007) | 2.015 (0.007) | 2.010 (0.021) |
| cross_ratio（越低越隔离） | 0.038 (0.007) | 0.022 (0.007) | 0.027 (0.020) |

三种语言下 political affiliation 的 same_ratio 几乎完全一致（1.999~2.015），说明这个偏差与 prompt 语言无关，是模型本身的特性。

## 生成成本

zh/ja 各 50/50 次调用一次成功解析，单网络耗时约 1,695~1,777 秒（28~30 分钟）；en 的耗时记录来自更早的一批调用，未保留完整 cost 数据（`stats/en/cost_stats_s1-2.csv` 只有 seed 1/2）。

## 结论

- **political affiliation 同质性偏差与 prompt 语言无关**：无论用英文、中文还是日文提问，same_ratio 都稳定在约 2.0，是三种语言里最一致的一个维度；其余维度（age/gender/race/religion，未在此列出，详见 `stats/{en,zh,ja}/homophily.csv`）在不同语言下有更明显的波动。
- 网络密度呈 en > zh > ja 的顺序，日文条件下模型更"惜友"，倾向选更少的朋友，网络也因此更分散（modularity 更高、平均最短路径更长）。
- 关于社区结构（louvain 社区数/大小）和友谊数不平等度（标准差/基尼系数）等更细的分析,详见 `PROGRESS_ja.md`（2026-07-24 会话记录),本 README 只汇总了核心结构与同质性指标。
- **注意**:样本量仅各语言 n=3,结论(尤其是密度随语言变化的趋势)置信度有限。

## 文件说明

- `networks/{en,zh,ja}/`:各语言生成的网络邻接表(`.adj`)
- `plots/{en,zh,ja}/`:各语言的网络可视化
- `stats/{en,zh,ja}/network_metrics.csv`、`homophily.csv`:结构指标与同质性原始数据
- `stats/{en,zh,ja}/cost_stats_s1-2.csv`:生成耗时与 token 用量(部分种子)

原始文件也仍保留在仓库常规路径下(`text-files/sequential_ollama/gemma4:e4b{,_zh,_ja}_*`、`plots/sequential_ollama/gemma4:e4b{,_zh,_ja}*`、`stats/sequential_ollama/gemma4:e4b{,_zh,_ja}/`),本文件夹是汇总副本,方便按语言单独查看这次实验的结果。
