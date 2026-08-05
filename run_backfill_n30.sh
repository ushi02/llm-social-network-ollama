#!/usr/bin/env bash
#
# 把 qwen3.5:9b 和 gemma4:e4b 的 w_interests 实验从 n=3 补到 n=30。
#
# 背景：这两组之前只跑了 seed 0/1/2（n=3），方差估计不足，置信度有限。
# 原论文 GPT-3.5 主设置是 n=30，这里补跑 seed 3..29（再补 27 个），凑齐 n=30。
#
# 重要：本脚本必须在**能访问 DGX Ollama 服务（10.236.129.210）的机器上**运行，
#       云端 Claude Code 会话访问不了该内网地址，跑不了。
#
# 用法：
#   bash run_backfill_n30.sh            # 两个模型都补
#   bash run_backfill_n30.sh qwen       # 只补 qwen3.5:9b（约 1 小时）
#   bash run_backfill_n30.sh gemma      # 只补 gemma4:e4b（约 16+ 小时，建议 nohup）
#
# 跑完后产物会落在仓库常规路径下（seed 3..29 与现有 0/1/2 并列）：
#   text-files/sequential_ollama/<model>_w_interests_{3..29}.adj
#   plots/sequential_ollama/<model>_w_interests_{3..29}.png
#   stats/sequential_ollama/<model>_w_interests/{homophily,network_metrics}.csv
#   stats/sequential_ollama/<model>_w_interests/cost_stats_s3-29.csv
# 之后再把这些 push 上来，我负责重新汇总到 *_results 文件夹并更新对比数据。

set -euo pipefail

export OLLAMA_BASE_URL="${OLLAMA_BASE_URL:-http://10.236.129.210:11434/v1}"

START_SEED=3
NUM=27   # seed 3..29 -> 27 个新网络，加上已有 0/1/2 = 30

run_qwen() {
  echo ">>> [qwen3.5:9b] 补跑 seed ${START_SEED}..$((START_SEED+NUM-1))（reasoning 已关闭，约 2 分钟/网络）"
  python generate_networks.py sequential \
    --model ollama/qwen3.5:9b \
    --persona_fn us_50_gpt4o_w_interests.json \
    --include_interests \
    --start_seed "${START_SEED}" \
    --num_networks "${NUM}" \
    --verbose
}

run_gemma() {
  echo ">>> [gemma4:e4b] 补跑 seed ${START_SEED}..$((START_SEED+NUM-1))（约 37 分钟/网络，总计很久，建议 nohup 后台跑）"
  python generate_networks.py sequential \
    --model ollama/gemma4:e4b \
    --persona_fn us_50_gpt4o_w_interests.json \
    --include_interests \
    --start_seed "${START_SEED}" \
    --num_networks "${NUM}" \
    --verbose
}

case "${1:-all}" in
  qwen)  run_qwen ;;
  gemma) run_gemma ;;
  all)   run_qwen; run_gemma ;;
  *) echo "未知参数: $1（可选 qwen | gemma | all）"; exit 1 ;;
esac

echo ">>> 完成。请检查上面列出的输出路径，然后 git add / commit / push。"
