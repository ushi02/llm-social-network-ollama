# 项目进展说明（截至 2026-07-17）

本文档基于 git 历史、未提交的改动、以及最近两次 Claude Code 会话记录整理，说明 `llm-social-network-ollama` 这个仓库目前做到了哪一步。

## 项目背景

这是 ICWSM 2025 论文 ["LLMs generate structurally realistic social networks but overestimate political homophily"](https://arxiv.org/abs/2408.16629) 的 fork 仓库。核心结论是：LLM 生成的社交网络在结构上较真实，但会**高估政治立场的同质性**（homophily）。这个 fork 之前已经加过 Ollama 支持（commit `fcbfa83`，2026-04-26），并跑过 `gemma4:26b`（带 `--include_reason`）、`gemma4:e4b`、`qwen3.5:9b` 的实验，结果已提交到仓库里。

## 这次会话做了什么

1. **摸清 DGX 上的 Ollama 服务**：确认开发机没有 GPU 也没有免密 sudo，改为直连已经跑在 DGX 上的 Ollama 服务 `http://10.236.129.210:11434`（OpenAI 兼容接口 `/v1`）。上面可用模型包括 `qwen3.5:9b`、`qwen3.5:27b`、`gemma4:e4b`、`gemma4:26b`、`gemma4:31b`、`mistral-small3.2:24b`、`nemotron:70b`、`hermes3:8b`、`gpt-oss:20b`、`gpt-oss:120b` 等。
2. **踩过的坑**：一开始尝试本地下载安装 Ollama（曾试图拉 `llama3.2:3b`），后来发现没必要，直接改用 DGX 的服务即可。
3. **代码改动**：`constants_and_utils.py` 的 `get_llm_response()` 里，Ollama 分支的 `base_url` 从硬编码的 `http://localhost:11434/v1` 改成读环境变量 `OLLAMA_BASE_URL`（没设置时才 fallback 到 localhost）。**这个改动目前还没有提交（unstaged）**。
4. **跑了新实验**：用 `sequential` 方法、`gemma4:e4b` 模型、带 `--include_interests`，生成了 3 个网络（seed 0/1/2），产物包括：
   - `text-files/sequential_ollama/gemma4:e4b_w_interests_{0,1,2}.adj`
   - `plots/sequential_ollama/gemma4:e4b_w_interests_{0,1,2}.png`
   - `stats/sequential_ollama/gemma4:e4b_w_interests/`、`stats/sequential_ollama_gemma4-e4b_w_interests/`
   
   这些都是**未提交的 untracked 文件**。
5. **分析对比**：用 `analyze_networks.py` / `plotting.py` 对新生成的 3 个网络做了同质性（homophily）分析，并和仓库里已有的 GPT-3.5（30 个网络，同样设置）做了对比，还做了一版可视化图表（[artifact 链接](https://claude.ai/code/artifact/be3eaa13-0d65-4550-a61d-8443eae20d79)，可能已过期需要重新生成）。

## 核心发现

拿 3 个 `gemma4:e4b` 网络 vs. GPT-3.5 的 30 个网络，对比 5 个人口统计维度的同质性：

- **政治立场差距巨大**：GPT-3.5 的 cross_ratio ≈ 0.30，`gemma4:e4b` 只有 **0.023 ± 0.010**——网络里的人几乎只跟同党派的人做朋友，比 GPT-3.5 极端得多。三次独立跑出来的结果高度一致（标准差很小），不像是偶然。
- 年龄、性别、种族、宗教这几个维度，两个模型差不多，没有类似量级的差异。
- 结构性指标（聚类系数、密度、模块度）上，`gemma4:e4b` 生成的网络比真实网络和 GPT-3.5 都更"抱团"，但整体形态合理（全连通、有社区结构）。

**结论**：这次实验基本复现并放大了原论文的核心结论——"LLM 生成的网络会高估政治同质性"——换成更小的开源模型（`gemma4:e4b`，约 4B 参数）后，这个偏差比 GPT-3.5 更严重。

**注意**：目前只有 n=3 的小样本，结论的置信度有限。

## 当前仓库状态

```
分支: agent（与 origin/agent 同步）

未提交的改动:
  modified:   constants_and_utils.py   （OLLAMA_BASE_URL 环境变量改动，见上）
  modified:   __pycache__/*.pyc        （编译产物，可忽略）

未跟踪的新文件:
  plots/sequential_ollama/gemma4:e4b_w_interests_{0,1,2}.png
  text-files/sequential_ollama/gemma4:e4b_w_interests_{0,1,2}.adj
  stats/sequential_ollama/gemma4:e4b_w_interests/
  stats/sequential_ollama_gemma4-e4b_w_interests/
```

这些改动和新文件还没有 commit，需要的话可以整理后提交。

## 会话结束时悬而未决的问题

上次会话结束时，助手向用户抛出的问题是：**接下来往哪个方向继续？** 给出的选项包括：

1. 多跑几个 seed，把样本量从 n=3 提高，增强结论置信度；
2. 换其他模型（比如 `qwen3.5:9b`、`hermes3:8b`）试试，看这个"政治同质性偏差被放大"的现象是 gemma4 系列特有的，还是更小的开源模型普遍存在的问题。

## 参考信息

- DGX Ollama 服务地址：`http://10.236.129.210:11434/v1`（跑之前建议先用 curl 测一下延迟，是共享资源，速度不稳定——之前测过 `qwen3.5:9b` 巨慢（约 1 token/s，疑似排队），`gemma4:e4b` 较快（热身后约 3-4s/次调用））。
- 使用方式：`export OLLAMA_BASE_URL="http://10.236.129.210:11434/v1"`，然后 `--model ollama/<model_name>` 照常跑。
