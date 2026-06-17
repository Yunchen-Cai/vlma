#!/usr/bin/env bash
set -euo pipefail

ROOT=/mnt/workspace/users/caiyunchen/vlma
PYCACHE=/mnt/workspace/users/caiyunchen/tmp/pycache
EVAL_GPU=${EVAL_GPU:-7}

cd "$ROOT"

log() {
  printf '[fourpart-queue] %s\n' "$1"
}

wait_for_model() {
  local model_dir="$1"
  while [[ ! -f "python/output/${model_dir}/config.json" ]]; do
    sleep 60
  done
}

run_eval() {
  local model_dir="$1"
  local eval_name="$2"
  local eval_files="$ROOT/python/data/roi_experiment_v2_4part/eval/test_full_v1.json,$ROOT/python/data/roi_experiment_v2_4part/eval/test_roi_v1.json"
  local image_root="$ROOT/python/data/roi_experiment_v2_4part"
  mkdir -p "python/output/eval/${eval_name}"
  log "evaluating ${model_dir} -> ${eval_name}"
  PYTHONPYCACHEPREFIX="$PYCACHE" \
  TRANSFORMERS_NO_TF=1 USE_TF=0 CUDA_VISIBLE_DEVICES="$EVAL_GPU" \
  VLM_MODEL_ID="$ROOT/python/output/${model_dir}" \
  VLM_EVAL_EXPERIMENT_NAME="$eval_name" \
  VLM_EVAL_FILES="$eval_files" \
  VLM_IMAGE_ROOT="$image_root" \
  python python/src/evaluate_model.py \
    > "python/output/eval/${eval_name}/eval.log" 2>&1
  PYTHONPYCACHEPREFIX="$PYCACHE" \
  python python/src/compute_verification_metrics.py \
    "$ROOT/python/output/eval/${eval_name}" \
    >> "python/output/eval/${eval_name}/eval.log" 2>&1
}

log "waiting for fourpart_full_roi_mixed_fullsft_v2_rerun"
wait_for_model "fourpart_full_roi_mixed_fullsft_v2_rerun"
wait_for_model "fourpart_roi_only_fullsft_v2_rerun"

run_eval "fourpart_roi_only_fullsft_v2_rerun" "fourpart_roi_only_fullsft_v2_rerun_eval_fourpart"
run_eval "fourpart_full_roi_mixed_fullsft_v2_rerun" "fourpart_full_roi_mixed_fullsft_v2_rerun_eval_fourpart"

log "queue completed"
