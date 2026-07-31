# 实验知识文档：LLM 生成社交网络 & 指标详解

给刚入门的你看的、关于这个仓库在做什么、怎么做、以及每个指标是什么意思的详细说明。

## 1. 论文在问什么

这个仓库是 ICWSM 2025 论文 ["LLMs generate structurally realistic social networks but overestimate political homophily"](https://arxiv.org/abs/2408.16629) 的 fork（作者：Serina Chang 等，斯坦福）。

核心问题：**如果让 LLM 扮演一群"人"，自己决定"我要跟谁做朋友"，它生成出来的社交网络，像不像真实世界的社交网络？**

这个问题有实际意义——现在很多计算社会科学研究开始用 LLM 模拟人群做实验（比如模拟舆论传播、政策效果、疫情扩散），这些研究的前提是"LLM 模拟出的社会结构要靠谱"。如果 LLM 生成的网络在某些方面系统性地偏离真实网络，那么建立在它之上的下游研究结论也会跟着偏。

论文的结论分两部分：

1. **好消息**：LLM（论文里用 GPT-3.5/GPT-4）生成的网络，在很多结构性指标上（度数分布、聚类系数、社区结构等）跟真实社交网络相当接近。
2. **坏消息**：LLM 生成的网络**系统性地高估了政治立场上的同质性**（political homophily）——也就是说，LLM 扮演的人几乎只跟同党派的人交朋友，比真实世界中人们的政治同质性明显更极端。这个偏差在其他人口统计维度（年龄、性别、种族、宗教）上不明显，唯独政治立场特别突出。

这个 fork 在原论文基础上加了 Ollama 支持，方便跑本地/自托管的开源模型（`gemma4`、`qwen3.5`、`mistral` 等），看看这个"政治同质性被高估"的现象是不是 GPT 系列特有的，还是更广泛存在于各种 LLM 里。目前仓库里的实验结果（见第 6 节）显示：**换成更小的开源模型后，这个偏差不但复现了，甚至比 GPT-3.5 更严重**。

## 2. 整体流程：三步走

```
第一步：生成 persona（人设）  →  generate_personas.py
第二步：生成网络（LLM 决定谁跟谁是朋友） →  generate_networks.py
第三步：分析网络，计算各种指标  →  analyze_networks.py
```

### 2.1 生成 persona

`generate_personas.py` 会按照美国人口普查数据的联合分布（性别 × 种族 × 年龄，见 `get_gender_race_age_cdf()`）采样出一批"人"，每个人有以下字段：

| 字段 | 说明 | 可能取值 |
|---|---|---|
| `gender` | 性别 | Man / Woman / Nonbinary |
| `age` | 年龄 | 0~100（按人口普查分布采样） |
| `race/ethnicity` | 种族/民族 | White / Black / Hispanic / Asian / American Indian-Alaska Native / Native Hawaiian-Pacific Islander |
| `religion` | 宗教 | Protestant / Catholic / Unreligious |
| `political affiliation` | 政党倾向 | Democrat / Republican |
| `name`（可选） | 姓名，用 `--include_names` 生成 | 由 LLM 根据人口统计特征生成 |
| `interests`（可选） | 兴趣爱好，用 `--include_interests` 生成 | 由 LLM 根据人口统计特征生成 |

仓库里实际用的是已经生成好的 50 人 persona 文件 `text-files/us_50_gpt4o_w_interests.json`（用 GPT-4o 生成的名字和兴趣），所有实验都复用这一份，保证跨模型可比。

### 2.2 生成网络：四种方法

`generate_networks.py` 的核心逻辑是：**把每个 persona 的信息喂给 LLM，让 LLM 以第一人称"扮演"这个人，自己决定交朋友**。有四种不同的"喂法"（`method` 参数）：

| 方法 | 怎么问 LLM | 调用次数 |
|---|---|---|
| `global` | 一次性把所有人的列表给 LLM，让它直接输出整个网络的所有好友对 | 1 次（但对小模型来说难度最高，格式最容易出错） |
| `local` | 逐个人处理：把这个人的 persona + 其他所有人的列表给 LLM，让 LLM（扮演这个人）从列表里选出朋友 | N 次（N=人数） |
| `sequential` | 跟 `local`类似，但按顺序逐个"加入"网络——每个人在选朋友时，能看到**已经加入的人当前有几个朋友**（`# friends`），这样能形成"富者愈富"的择优连接效应（preferential attachment），更像真实社交网络的形成过程 | N 次 |
| `iterative` | 先用 `local` 建立一个初始网络，然后反复迭代：每一轮，每个人都被问"你要新加一个朋友吗"和"你要断绝一个朋友吗"，这样网络会不断被"重连" | 建立阶段 N 次 + 每轮迭代 2N 次 × `num_iter` 轮 |

**原论文和这个仓库里的实验大多用 `sequential` 方法**，因为它既能体现现实中"朋友圈是一点点建立起来的"这个过程，调用次数也比 `iterative` 少。

每次调用的 prompt 结构（以 `sequential` 为例）：

- **System prompt**：告诉 LLM"你是 [persona 描述]，你正在加入一个社交网络"，然后列出候选朋友的信息（人口统计特征 + 当前好友数），要求"请以 ID,ID,ID 的格式列出你的朋友，只能包含数字和逗号"。
- **User prompt**：候选人列表本身（每人一行，格式如 `28. Man, age 48, Hispanic, Protestant, Democrat, interests include: ...; has 9 friends`）。
- LLM 的回复会被解析成边（friendship edges），加到图里。如果解析失败（比如格式不对、ID 不存在），会重新问一次（`repeat_prompt_until_parsed`，`generate_networks.py` 里生成结果附带的 `num_tries` 就是重试次数，正常应该等于人数，即每人一次成功）。

### 2.3 关键命令行参数

```
python generate_networks.py sequential --model ollama/gemma4:e4b \
    --persona_fn us_50_gpt4o_w_interests.json --include_interests \
    --num_networks 3 --start_seed 0
```

| 参数 | 作用 |
|---|---|
| `method`（位置参数） | `global` / `local` / `sequential` / `iterative` |
| `--model` | 用哪个模型，本地 Ollama 模型要加 `ollama/` 前缀（如 `ollama/gemma4:e4b`） |
| `--persona_fn` | 用哪份 persona 文件 |
| `--include_interests` | prompt 里加入每个人的兴趣爱好（这是**原论文的标准设置**，也是本仓库大部分实验用的设置） |
| `--include_names` | prompt 里加入姓名（会带来种族/性别相关的隐含信息） |
| `--include_reason` | 让 LLM 除了给出朋友列表，还要给出交朋友的理由（存成 `_reasons.json`，用来做质性分析） |
| `--mean_choices` | 限制每人一次最多选几个朋友（指数分布采样，不设置则不限制） |
| `--lang` | `en`/`zh`/`ja`，prompt 语言（本仓库额外加的功能，原论文只有英文） |
| `--num_networks` / `--start_seed` | 生成几个网络（几个随机种子），用于估计结果的方差（论文里 GPT-3.5 用 n=30，本仓库大部分开源模型实验因为跑得慢，用 n=3） |
| `--temp` | 采样温度 |

每次运行的产物：

- `text-files/{method}_{model}_{seed}.adj`：生成的网络（邻接表）
- `plots/{method}_{model}_{seed}.png`：网络可视化
- `stats/{method}_{model}/cost_stats_s{start}-{end}.csv`：耗时、token 用量、重试次数

## 3. 分析网络：`analyze_networks.py`

生成完网络后，用这个脚本计算各种指标，全部汇总进两个 csv：`network_metrics.csv`（结构性+节点级指标）和 `homophily.csv`（同质性指标）。

### 3.1 结构性指标（整张图一个数）

| 指标 | 含义 | 怎么算 |
|---|---|---|
| `density` | 网络密度：实际边数 / 所有可能边数 | `nx.density` |
| `avg_clustering_coef` | 平均聚类系数：你的朋友们互相也是朋友的程度（"物以类聚"的强度） | `nx.average_clustering` |
| `prop_nodes_lcc` | 最大连通分量（giant component）占全部节点的比例——网络是不是"整体连成一片"还是分成好几个互不来往的孤岛 | 自定义 `prop_nodes_in_giant_component` |
| `radius` / `diameter` | 最大连通分量内的图半径/直径（网络"有多大"，按标准化后的图距离衡量），除以 `log(节点数)` 做归一化，方便跨不同规模的网络比较 | `nx.radius` / `nx.diameter`，仅在最大连通分量上算 |
| `avg_shortest_path` | 平均最短路径长度（六度分隔那个概念），同样在最大连通分量上算并归一化 | `nx.average_shortest_path_length` |
| `modularity` | 社区结构的强弱：用 Louvain 算法先找出社区（`nx.community.louvain_communities`），再算模块度——数值越高，说明网络越明显地分成一个个"小圈子"，圈子内部连接紧密、圈子之间连接稀疏 | `nx.community.modularity` |

**怎么读这些数字**：这些都是跟"真实社交网络"（仓库自带 `real_networks/` 下的数据，来自 Add Health 等真实社会网络数据集）做对比用的。如果 LLM 生成网络的这些指标跟真实网络接近，说明"结构上像真的"；差异大就说明 LLM 生成的网络在密度、抱团程度、连通性上跟现实脱节。

### 3.2 节点级指标（每个人一个数）

| 指标 | 含义 |
|---|---|
| `degree_centrality` | 这个人朋友数占理论最大朋友数的比例——越高越是"社交达人" |
| `betweenness_centrality` | 这个人在多少条"别人到别人的最短路径"上——越高说明这个人是连接不同社交圈子的"桥梁" |
| `closeness_centrality` | 这个人到网络里所有其他人的平均距离的倒数——越高说明这个人在网络里越"中心" |

### 3.3 同质性（homophily）指标——这是论文的核心

**同质性**指的是"物以类聚"：人是不是倾向于跟自己人口统计特征相同的人交朋友。用来量化的两个核心指标：

**`same_ratio`（观察到的"同类朋友"比例 / 随机情况下期望的比例）**

```
same_ratio = 实际网络中"同类"边的占比 / 完全图（所有人两两都是朋友）中"同类"边的占比
```

- 对于二元/类别型特征（性别、种族、宗教、政党）："同类"指两人该字段完全相同。
- 对于 `age`：不要求完全相同，而是"年龄差 ≤ 10 岁"算同类。
- `same_ratio = 1.0` 表示"完全随机"——交朋友完全不看这个特征。
- `same_ratio > 1.0` 表示存在同质性倾向，数值越大，越倾向于只跟"自己人"做朋友。例如 `same_ratio(political affiliation) = 2.0` 表示：网络里同党派好友对出现的频率，是"完全随机交友"情况下的 2 倍。

**`cross_ratio`（观察到的"跨类朋友"比例 / 随机期望）**——同质性的另一面

```
cross_ratio = 实际网络中"跨类"边的占比（对 age 是平均年龄差） / 完全图中的期望值
```

- `cross_ratio = 1.0` 表示随机；**`cross_ratio` 越接近 0，说明这个群体越"自我隔离"**——几乎不跟其他类别的人交朋友。
- 论文和本仓库实验里反复出现的关键数字：`political affiliation` 的 `cross_ratio`，GPT-3.5 大约 0.30，本仓库测的开源小模型（gemma4:e4b）只有 0.02~0.03——**意味着网络里的共和党人和民主党人之间的跨党派友谊，比 GPT-3.5 生成的还要少一个数量级**，其他人口统计维度（年龄、性别、种族、宗教）则没有这种极端现象。

**两两分组的详细版本**：`compute_pairwise_ratios()` 会算出任意两个具体群体之间（比如"白人-黑人"“共和党-共和党”）的观察/期望比例矩阵，比 `same_ratio`/`cross_ratio` 更细粒度，能看出比如"是不是所有跨党派连接都被压低了，还是只是某些特定党派内部更抱团"。

### 3.4 政治相关的专门指标

这两个不在默认的 `summarize_network_metrics()` 里跑，是单独的函数，出自另外两篇被引用的论文：

- **`compute_isolation_index`**（Halberstam & Knight, 2016）：衡量"信息隔离"——保守派（Republican）平均看到的"保守派邻居比例"，减去自由派（Democrat）平均看到的"保守派邻居比例"。数值越大，说明两派人在网络里活在越不同的"信息茧房"里。
- **`compute_polarization`**（Garimella & Weber, 2017）：给每个节点算一个"political lean"分数（根据邻居中民主党/共和党的比例，贝叶斯平滑过），再取偏离 0.5（中立）的距离 × 2，得到每个节点的极化程度（0=完全中立混合邻居，1=邻居全是同一党派）。

### 3.5 边级别的指标

- `get_edge_proportions` / `compute_edge_distance`：给定同一设置下生成的多个网络（比如同一模型跑的 n=3 个种子），看这些网络彼此之间"哪些边总是出现"“哪些网络之间差异有多大”——用来判断 LLM 生成网络的**随机性/一致性**：如果同一模型每次跑出来的网络几乎一样，说明它其实没怎么"随机决策"，可能是在套用一个固定的模式。

## 4. 怎么读一份实验结果（以仓库里已有的为例）

仓库根目录下的 `*_results/` 文件夹（`gemma4-26b_w_reason_results`、`gemma4-e4b_w_interests_results`、`gemma4-e4b_lang_results`、`mistral-small3.2-24b_results`、`qwen3.5-9b_w_interests_results`）是已经跑完并整理好的实验，每个文件夹都有自己的 `README.md`，结构一致：

```
networks/   生成的网络原始文件（.adj），以及 --include_reason 的话还有 _reasons.json
plots/      网络可视化图
stats/      network_metrics.csv、homophily.csv（本节讲的所有指标都在这里）、cost_stats（生成耗时）
README.md   人话版的结果总结：跟 GPT-3.5 基线对比的表格 + 结论
```

想知道"这个模型生成的网络政治同质性有多夸张"，直接打开对应文件夹的 `README.md` 看 `political affiliation` 那一行的 `same_ratio`/`cross_ratio` 就行；想自己重新算或者做别的对比，去 `stats/homophily.csv` 里筛数据。

## 5. 参考

- 论文原文：["LLMs generate structurally realistic social networks but overestimate political homophily"](https://arxiv.org/abs/2408.16629)（ICWSM 2025）
- 项目此前的阶段性记录：`PROGRESS.md`（2026-07-17，中文）、`PROGRESS_ja.md`（2026-07-24，日文）——记录了具体跑实验时踩的坑（比如 Ollama thinking 模型卡住的问题），跟本文档的"是什么/怎么算"角度是互补的。
- DGX Ollama 服务：`http://10.236.129.210:11434`，共享资源，跑之前建议先测一下延迟。
