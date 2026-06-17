#!/usr/bin/env bash
set -euo pipefail

ROOT=/mnt/workspace/users/caiyunchen/vlma
cd "$ROOT"

sizes=(50 100 200 300 400)
for size in "${sizes[@]}"; do
  case "$size" in
    50) epochs=12 ;;
    100) epochs=8 ;;
    200) epochs=6 ;;
    300|400) epochs=4 ;;
    *) epochs=4 ;;
  esac

  bash python/src/run_single_pipeline.sh \
    "/mnt/workspace/users/caiyunchen/vlma/python/data/roi_experiment_v1/fewshot/full_sft_v1_${size}.json" \
    "cover_full_only_fs${size}" \
    "$epochs"

  bash python/src/run_single_pipeline.sh \
    "/mnt/workspace/users/caiyunchen/vlma/python/data/roi_experiment_v1/fewshot/roi_only_sft_v1_${size}.json" \
    "cover_roi_only_fs${size}" \
    "$epochs"
done
