#!/usr/bin/env bash
set -euo pipefail

ROOT=/mnt/workspace/users/caiyunchen/vlma
PYCACHE=/mnt/workspace/users/caiyunchen/tmp/pycache
TRAIN_GPUS=${TRAIN_GPUS:-0,1,2,3,4,5,6,7}
TRAIN_NPROC=${TRAIN_NPROC:-8}
EVAL_GPU=${EVAL_GPU:-0}
NUM_EPOCHS=${NUM_EPOCHS:-4}

DATA_ROOT="$ROOT/python/data/unified_no_phase_v1"
GENERAL_TRAIN="$ROOT/python/data/clean_assembly_sft_12.23merged.json"
GENERAL_EVAL="$ROOT/python/data/1.26.test.json"
VERIF_FULL="$ROOT/python/data/roi_experiment_v2_4part/sft/full_sft_v1.json"
VERIF_MIXED="$ROOT/python/data/roi_experiment_v2_4part/sft/full_roi_mixed_sft_v1.json"
FOURPART_EVAL_FILES="$ROOT/python/data/roi_experiment_v2_4part/eval/test_full_v1.json,$ROOT/python/data/roi_experiment_v2_4part/eval/test_roi_v1.json"
FOURPART_IMAGE_ROOT="$ROOT/python/data/roi_experiment_v2_4part"

cd "$ROOT"

log() {
  printf '[unified-no-phase] %s\n' "$1"
}

build_datasets() {
  log "building no-phase datasets"
  PYTHONPYCACHEPREFIX="$PYCACHE" python python/src/build_unified_no_phase_dataset.py \
    --general-train "$GENERAL_TRAIN" \
    --general-eval "$GENERAL_EVAL" \
    --verification-full "$VERIF_FULL" \
    --verification-mixed "$VERIF_MIXED" \
    --output-root "$DATA_ROOT"
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
  if [[ -f "python/output/${experiment_name}/config.json" ]]; then
    log "model already finalized: ${experiment_name}"
    return 0
  fi
  log "training: ${experiment_name}"
  CUDA_VISIBLE_DEVICES="$TRAIN_GPUS" \
  NPROC="$TRAIN_NPROC" \
  bash python/src/run_train_only_pipeline.sh "$data_file" "$experiment_name" "$NUM_EPOCHS"
}

run_general_eval() {
  local model_dir="$1"
  local eval_name="$2"
  log "general ATP eval: ${eval_name}"
  mkdir -p "python/output/eval/${eval_name}"
  PYTHONPYCACHEPREFIX="$PYCACHE" \
  TRANSFORMERS_NO_TF=1 USE_TF=0 CUDA_VISIBLE_DEVICES="$EVAL_GPU" \
  VLM_MODEL_ID="$ROOT/python/output/${model_dir}" \
  VLM_EVAL_EXPERIMENT_NAME="$eval_name" \
  VLM_EVAL_FILES="$DATA_ROOT/eval/general_atp_only_eval_v1.json" \
  python python/src/evaluate_general_atp_model.py \
    > "python/output/eval/${eval_name}/eval.log" 2>&1
}

run_verification_eval() {
  local model_dir="$1"
  local eval_name="$2"
  log "verification eval: ${eval_name}"
  mkdir -p "python/output/eval/${eval_name}"
  PYTHONPYCACHEPREFIX="$PYCACHE" \
  TRANSFORMERS_NO_TF=1 USE_TF=0 CUDA_VISIBLE_DEVICES="$EVAL_GPU" \
  VLM_MODEL_ID="$ROOT/python/output/${model_dir}" \
  VLM_EVAL_EXPERIMENT_NAME="$eval_name" \
  VLM_EVAL_FILES="$FOURPART_EVAL_FILES" \
  VLM_IMAGE_ROOT="$FOURPART_IMAGE_ROOT" \
  python python/src/evaluate_model.py \
    > "python/output/eval/${eval_name}/eval.log" 2>&1
  PYTHONPYCACHEPREFIX="$PYCACHE" \
  python python/src/compute_verification_metrics.py \
    "$ROOT/python/output/eval/${eval_name}" \
    >> "python/output/eval/${eval_name}/eval.log" 2>&1
}

build_datasets

ATP_ONLY_EXP="unified_nophase_atp_only_fullsft_v1"
ATP_FULL_EXP="unified_nophase_atp_plus_fullverif_fullsft_v1"
ATP_MIXED_EXP="unified_nophase_atp_plus_fullroimixed_fullsft_v1"

train_if_needed "$DATA_ROOT/sft/general_atp_only_sft_v1.json" "$ATP_ONLY_EXP"
run_general_eval "$ATP_ONLY_EXP" "${ATP_ONLY_EXP}_eval_126_atp"
run_verification_eval "$ATP_ONLY_EXP" "${ATP_ONLY_EXP}_eval_fourpart"

train_if_needed "$DATA_ROOT/sft/general_plus_verification_full_sft_v1.json" "$ATP_FULL_EXP"
run_general_eval "$ATP_FULL_EXP" "${ATP_FULL_EXP}_eval_126_atp"
run_verification_eval "$ATP_FULL_EXP" "${ATP_FULL_EXP}_eval_fourpart"

train_if_needed "$DATA_ROOT/sft/general_plus_verification_full_roi_mixed_sft_v1.json" "$ATP_MIXED_EXP"
run_general_eval "$ATP_MIXED_EXP" "${ATP_MIXED_EXP}_eval_126_atp"
run_verification_eval "$ATP_MIXED_EXP" "${ATP_MIXED_EXP}_eval_fourpart"

log "queue completed"
