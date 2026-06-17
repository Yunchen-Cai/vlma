#!/usr/bin/env bash
set -euo pipefail

ROOT=/mnt/workspace/users/caiyunchen/vlma
PYCACHE=/mnt/workspace/users/caiyunchen/tmp/pycache
TRAIN_GPUS=${TRAIN_GPUS:-0,1,2,3}
TRAIN_NPROC=${TRAIN_NPROC:-4}
EVAL_GPU=${EVAL_GPU:-0}

cd "$ROOT"

log() {
  printf '[queue] %s\n' "$1"
}

wait_for_model() {
  local model_dir="$1"
  while [[ ! -f "python/output/${model_dir}/config.json" ]]; do
    sleep 60
  done
}

train_if_needed() {
  local data_file="$1"
  local experiment_name="$2"
  local num_epochs="${3:-4}"
  if [[ -f "python/output/${experiment_name}/config.json" ]]; then
    log "model already finalized: ${experiment_name}"
    return 0
  fi
  if [[ -f "python/output/${experiment_name}/train.log" ]]; then
    log "model appears to be running already, waiting: ${experiment_name}"
    wait_for_model "$experiment_name"
    return 0
  fi
  log "training: ${experiment_name}"
  CUDA_VISIBLE_DEVICES="$TRAIN_GPUS" \
  NPROC="$TRAIN_NPROC" \
  bash python/src/run_train_only_pipeline.sh "$data_file" "$experiment_name" "$num_epochs"
}

run_general_eval() {
  local model_dir="$1"
  local eval_name="$2"
  if [[ -f "python/output/eval/${eval_name}/summary.csv" ]]; then
    log "general eval already exists: ${eval_name}"
    return 0
  fi
  log "general eval: ${eval_name}"
  mkdir -p "python/output/eval/${eval_name}"
  PYTHONPYCACHEPREFIX="$PYCACHE" \
  TRANSFORMERS_NO_TF=1 USE_TF=0 CUDA_VISIBLE_DEVICES="$EVAL_GPU" \
  VLM_MODEL_ID="$ROOT/python/output/${model_dir}" \
  VLM_EVAL_EXPERIMENT_NAME="$eval_name" \
  VLM_EVAL_FILES="$ROOT/python/data/1.26.test.json" \
  python python/src/evaluate_general_model.py \
    > "python/output/eval/${eval_name}/eval.log" 2>&1
}

run_verification_eval() {
  local model_dir="$1"
  local eval_name="$2"
  local eval_files="$3"
  local image_root="$4"
  if [[ -f "python/output/eval/${eval_name}/metrics_summary.csv" ]]; then
    log "verification eval already exists: ${eval_name}"
    return 0
  fi
  log "verification eval: ${eval_name}"
  mkdir -p "python/output/eval/${eval_name}"
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

COVER_314_FILES="$ROOT/python/data/roi_experiment_cover_val_314/eval/test_full_v1.json,$ROOT/python/data/roi_experiment_cover_val_314/eval/test_roi_v1.json"
COVER_316_FILES="$ROOT/python/data/roi_experiment_cover_test_316/eval/test_full_v1.json,$ROOT/python/data/roi_experiment_cover_test_316/eval/test_roi_v1.json"
COVER_314_ROOT="$ROOT/python/data/roi_experiment_cover_val_314"
COVER_316_ROOT="$ROOT/python/data/roi_experiment_cover_test_316"

log "waiting for general_1223_fullsft_v1"
wait_for_model "general_1223_fullsft_v1"
run_general_eval "general_1223_fullsft_v1" "general_1223_eval_126_general"
run_verification_eval "general_1223_fullsft_v1" "general_1223_eval_314_plain" "$COVER_314_FILES" "$COVER_314_ROOT"
run_verification_eval "general_1223_fullsft_v1" "general_1223_eval_316_plain" "$COVER_316_FILES" "$COVER_316_ROOT"

train_if_needed \
  "$ROOT/python/data/multitask_experiment_v1/sft/general_plus_coverx_mixed_sft_v1.json" \
  "multitask_general_coverx_mixed_fullsft_v1" \
  4
run_general_eval "multitask_general_coverx_mixed_fullsft_v1" "multitask_general_coverx_mixed_eval_126_general"
run_verification_eval "multitask_general_coverx_mixed_fullsft_v1" "multitask_general_coverx_mixed_eval_314_plain" "$COVER_314_FILES" "$COVER_314_ROOT"
run_verification_eval "multitask_general_coverx_mixed_fullsft_v1" "multitask_general_coverx_mixed_eval_316_plain" "$COVER_316_FILES" "$COVER_316_ROOT"

train_if_needed \
  "$ROOT/python/data/multitask_experiment_v1/sft/general_plus_coverx_mixed_x2_sft_v1.json" \
  "multitask_general_coverx_mixed_x2_fullsft_v1" \
  4
run_general_eval "multitask_general_coverx_mixed_x2_fullsft_v1" "multitask_general_coverx_mixed_x2_eval_126_general"
run_verification_eval "multitask_general_coverx_mixed_x2_fullsft_v1" "multitask_general_coverx_mixed_x2_eval_314_plain" "$COVER_314_FILES" "$COVER_314_ROOT"
run_verification_eval "multitask_general_coverx_mixed_x2_fullsft_v1" "multitask_general_coverx_mixed_x2_eval_316_plain" "$COVER_316_FILES" "$COVER_316_ROOT"

log "queue completed"
