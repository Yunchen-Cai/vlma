#!/usr/bin/env bash
set -euo pipefail
DATA_FILE=${1:?DATA_FILE required}
EXPERIMENT_NAME=${2:?EXPERIMENT_NAME required}
NUM_EPOCHS=${3:-4}
MODEL_ID=${4:-/mnt/workspace/users/caiyunchen/vlma/python/models/Qwen2.5-VL-7B-Instruct}
NPROC=${NPROC:-8}
ROOT=/mnt/workspace/users/caiyunchen/vlma
PYCACHE=/mnt/workspace/users/caiyunchen/tmp/pycache
cd "$ROOT"
OUT="python/output/${EXPERIMENT_NAME}"
rm -rf "$OUT"
mkdir -p "$OUT"
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
echo "[pipeline] completed ${EXPERIMENT_NAME}"
