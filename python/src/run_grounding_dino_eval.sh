#!/usr/bin/env bash
# Run end-to-end Grounding DINO ROI provider evaluation (paper §4.3.2 / Block E supplement).
#
# Usage (on the remote box):
#   cd /mnt/workspace/users/caiyunchen/vlma
#   bash python/src/run_grounding_dino_eval.sh
#
# The script:
#   1. runs Grounding DINO Tiny on the four-part test set to produce detected
#      ROI crops + IoU stats + an SFT-style eval JSON;
#   2. runs evaluate_model.py against the Full+ROI mixed checkpoint on the
#      detector-produced ROI crops;
#   3. runs compute_verification_metrics.py to produce metrics_summary.csv.
#
set -euo pipefail

ROOT=/mnt/workspace/users/caiyunchen/vlma
PYCACHE=/mnt/workspace/users/caiyunchen/tmp/pycache
EVAL_GPU=${EVAL_GPU:-0}

# Use the same python interpreter the rest of the pipeline uses.
CONDA_PY=${CONDA_PY:-/mnt/workspace/envs/conda3/envs/starVLA_chidafeng/bin/python}

MODEL_NAME=${MODEL_NAME:-fourpart_full_roi_mixed_fullsft_v2_rerun}
MODEL_DIR="$ROOT/python/output/$MODEL_NAME"

DATA_ROOT="$ROOT/python/data/roi_experiment_v2_4part"
META_CSV="$DATA_ROOT/metadata/split_test_v1.csv"
GD_DIR="$ROOT/python/models/grounding-dino-tiny"
ROI_PY="$ROOT/python/src/run_grounding_dino_roi.py"
EVAL_PY="$ROOT/python/src/evaluate_model.py"
METRIC_PY="$ROOT/python/src/compute_verification_metrics.py"

EVAL_OUT_DIR="$DATA_ROOT/eval_grounding_dino"
EVAL_JSON="$EVAL_OUT_DIR/test_roi_grounding_dino_v1.json"
EVAL_NAME="grounding_dino_roi_provider_eval"

log() { printf '[gd-roi-eval] %s\n' "$1"; }

# 0. Sanity checks
[[ -f "$META_CSV"  ]] || { echo "Missing $META_CSV"; exit 2; }
[[ -d "$GD_DIR"    ]] || { echo "Missing Grounding DINO weights at $GD_DIR"; exit 2; }
[[ -f "$ROI_PY"    ]] || { echo "Missing $ROI_PY"; exit 2; }
[[ -f "$EVAL_PY"   ]] || { echo "Missing $EVAL_PY"; exit 2; }
[[ -f "$METRIC_PY" ]] || { echo "Missing $METRIC_PY"; exit 2; }
[[ -d "$MODEL_DIR" ]] || { echo "Missing model dir $MODEL_DIR"; exit 2; }

# 1. Produce detected ROI crops + IoU stats + eval JSON
if [[ ! -f "$EVAL_JSON" ]]; then
  log "running Grounding DINO Tiny on $META_CSV"
  cd "$ROOT"
  CUDA_VISIBLE_DEVICES=$EVAL_GPU \
  PYTHONPYCACHEPREFIX="$PYCACHE" \
  "$CONDA_PY" python/src/run_grounding_dino_roi.py \
    --csv "python/data/roi_experiment_v2_4part/metadata/split_test_v1.csv" \
    --image-root "python/data" \
    --model-dir "python/models/grounding-dino-tiny" \
    --out-dir "python/data/roi_experiment_v2_4part/eval_grounding_dino" \
    --crop-dir "python/data/roi_experiment_v2_4part/images_roi_bbox_grounding_dino"
else
  log "eval JSON already present at $EVAL_JSON, skipping detector pass"
fi

# 2. Run the VLM on the detector-produced ROI crops
log "running evaluate_model.py against $MODEL_NAME using detector ROIs"
cd "$ROOT"
TRANSFORMERS_NO_TF=1 USE_TF=0 \
CUDA_VISIBLE_DEVICES=$EVAL_GPU \
VLM_MODEL_ID="$MODEL_DIR" \
VLM_EVAL_EXPERIMENT_NAME="$EVAL_NAME" \
VLM_EVAL_FILES="$EVAL_JSON" \
PYTHONPYCACHEPREFIX="$PYCACHE" \
"$CONDA_PY" python/src/evaluate_model.py

# 3. Compute verification metrics
log "computing metrics with compute_verification_metrics.py"
cd "$ROOT"
PYTHONPYCACHEPREFIX="$PYCACHE" \
"$CONDA_PY" python/src/compute_verification_metrics.py \
  --pred-dir "python/output/eval/$EVAL_NAME" \
  --out "python/output/eval/$EVAL_NAME/metrics_summary.csv"

log "done. Results under python/output/eval/$EVAL_NAME/"
log "IoU summary: $EVAL_OUT_DIR/iou_summary.json"
