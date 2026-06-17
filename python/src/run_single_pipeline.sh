#!/usr/bin/env bash
set -euo pipefail

DATA_FILE=${1:?DATA_FILE required}
EXPERIMENT_NAME=${2:?EXPERIMENT_NAME required}
NUM_EPOCHS=${3:-4}
MODEL_ID=${4:-/mnt/workspace/users/caiyunchen/vlma/python/models/Qwen2.5-VL-7B-Instruct}
EVAL_FILES_ARG=${5:-}
IMAGE_ROOT_ARG=${6:-}
NPROC=${NPROC:-8}
ROOT=/mnt/workspace/users/caiyunchen/vlma
PYCACHE=/mnt/workspace/users/caiyunchen/tmp/pycache

cd "$ROOT"
OUT="python/output/${EXPERIMENT_NAME}"
EVAL_NAME="${EXPERIMENT_NAME}_eval"
EVAL_DIR="python/output/eval/${EVAL_NAME}"

rm -rf "$OUT" "$EVAL_DIR"
mkdir -p "$OUT" "$EVAL_DIR"

EVAL_FILES="${EVAL_FILES_ARG:-${VLM_EVAL_FILES:-}}"
IMAGE_ROOT="${IMAGE_ROOT_ARG:-${VLM_IMAGE_ROOT:-}}"

if [[ -z "$EVAL_FILES" ]]; then
  case "$DATA_FILE" in
    *roi_experiment_v2_4part*)
      EVAL_FILES="$ROOT/python/data/roi_experiment_v2_4part/eval/test_full_v1.json,$ROOT/python/data/roi_experiment_v2_4part/eval/test_roi_v1.json"
      IMAGE_ROOT="${IMAGE_ROOT:-$ROOT/python/data/roi_experiment_v2_4part}"
      ;;
    *roi_experiment_v1*)
      EVAL_FILES="$ROOT/python/data/roi_experiment_v1/eval/test_full_v1.json,$ROOT/python/data/roi_experiment_v1/eval/test_roi_v1.json"
      IMAGE_ROOT="${IMAGE_ROOT:-$ROOT/python/data/roi_experiment_v1}"
      ;;
  esac
fi

echo "[pipeline] training ${EXPERIMENT_NAME}"
PYTHONPYCACHEPREFIX="$PYCACHE" \
TRANSFORMERS_NO_TF=1 USE_TF=0 \
VLM_MODEL_ID="$MODEL_ID" \
VLM_DATA_FILE="$DATA_FILE" \
VLM_EXPERIMENT_NAME="$EXPERIMENT_NAME" \
VLM_NUM_TRAIN_EPOCHS="$NUM_EPOCHS" \
torchrun --standalone --nproc_per_node="$NPROC" python/src/full_sft_train.py \
  > "$OUT/train.log" 2>&1

if [[ ! -f "$OUT/config.json" ]]; then
  LATEST_CHECKPOINT=$(find "$OUT" -maxdepth 1 -type d -name 'checkpoint-*' | sed 's#.*/checkpoint-##' | sort -n | tail -1)
  if [[ -z "${LATEST_CHECKPOINT:-}" ]]; then
    echo "[pipeline] no final model and no checkpoint found for ${EXPERIMENT_NAME}" >&2
    exit 1
  fi
  echo "[pipeline] finalizing checkpoint-${LATEST_CHECKPOINT} for ${EXPERIMENT_NAME}"
  PYTHONPYCACHEPREFIX="$PYCACHE" \
  python python/src/finalize_checkpoint.py \
    "$OUT/checkpoint-${LATEST_CHECKPOINT}" \
    "$OUT" \
    "$MODEL_ID" \
    >> "$OUT/train.log" 2>&1
fi

echo "[pipeline] exporting loss ${EXPERIMENT_NAME}"
PYTHONPYCACHEPREFIX="$PYCACHE" python python/src/export_loss_curve.py "$OUT" >> "$OUT/train.log" 2>&1

if [[ -z "$EVAL_FILES" ]]; then
  echo "[pipeline] no evaluation files configured for ${EXPERIMENT_NAME}; skipping evaluation"
  echo "[pipeline] completed ${EXPERIMENT_NAME}"
  exit 0
fi

echo "[pipeline] evaluating ${EXPERIMENT_NAME}"
PYTHONPYCACHEPREFIX="$PYCACHE" \
TRANSFORMERS_NO_TF=1 USE_TF=0 CUDA_VISIBLE_DEVICES=0 \
VLM_MODEL_ID="/mnt/workspace/users/caiyunchen/vlma/$OUT" \
VLM_EVAL_EXPERIMENT_NAME="$EVAL_NAME" \
VLM_EVAL_FILES="$EVAL_FILES" \
VLM_IMAGE_ROOT="${IMAGE_ROOT:-$ROOT/python/data}" \
python python/src/evaluate_model.py > "$EVAL_DIR/eval.log" 2>&1

echo "[pipeline] computing metrics ${EXPERIMENT_NAME}"
PYTHONPYCACHEPREFIX="$PYCACHE" python python/src/compute_verification_metrics.py "$EVAL_DIR" >> "$EVAL_DIR/eval.log" 2>&1

echo "[pipeline] completed ${EXPERIMENT_NAME}"
