#!/usr/bin/env bash
# Run ROI provider sensitivity evaluation (paper §4.7).
#
# Usage (on the remote box):
#   cd /mnt/workspace/users/caiyunchen/vlma
#   bash python/src/run_roi_sensitivity_eval.sh
#
# Override env vars if needed:
#   EVAL_GPU=0 PERTURB_TAGS="c10 s10" bash python/src/run_roi_sensitivity_eval.sh
#
# The script:
#   1. builds the perturbed eval datasets (images + JSON) if missing;
#   2. runs evaluate_model.py against the Full+ROI mixed model on each tier;
#   3. runs compute_verification_metrics.py to produce metrics_summary.csv;
#   4. emits a consolidated CSV roi_sensitivity_summary.csv across tiers.
#
set -euo pipefail

ROOT=/mnt/workspace/users/caiyunchen/vlma
PYCACHE=/mnt/workspace/users/caiyunchen/tmp/pycache
EVAL_GPU=${EVAL_GPU:-0}
PERTURB_TAGS=${PERTURB_TAGS:-"c5 c10 c15 s10 s20"}

# Use the same Python interpreter as the unified eval queue
# (transformers 4.57 with Qwen2.5-VL support; the system /opt/conda
#  python only has transformers 4.51 and crashes on Qwen2_5_VL).
CONDA_PY=${CONDA_PY:-/mnt/workspace/envs/conda3/envs/starVLA_chidafeng/bin/python}

# Best Full+ROI mixed four-part checkpoint used in §4.5 of the paper.
MODEL_NAME=${MODEL_NAME:-fourpart_full_roi_mixed_fullsft_v2_rerun}
MODEL_DIR="$ROOT/python/output/$MODEL_NAME"

DATA_ROOT="$ROOT/python/data/roi_experiment_v2_4part"
META_CSV="$DATA_ROOT/metadata/split_test_v1.csv"
BUILDER="$ROOT/python/src/build_roi_perturb_dataset.py"
EVAL_PY="$ROOT/python/src/evaluate_model.py"
METRIC_PY="$ROOT/python/src/compute_verification_metrics.py"

log() { printf '[roi-sensitivity] %s\n' "$1"; }

# 0. Sanity checks
[[ -f "$META_CSV"        ]] || { echo "Missing $META_CSV"; exit 2; }
[[ -f "$BUILDER"         ]] || { echo "Missing $BUILDER"; exit 2; }
[[ -f "$EVAL_PY"         ]] || { echo "Missing $EVAL_PY"; exit 2; }
[[ -f "$METRIC_PY"       ]] || { echo "Missing $METRIC_PY"; exit 2; }
[[ -d "$MODEL_DIR"       ]] || { echo "Missing model dir $MODEL_DIR"; exit 2; }

# 1. Build perturbed datasets if any tier's eval JSON is missing
NEED_BUILD=0
for tag in $PERTURB_TAGS; do
  if [[ ! -f "$DATA_ROOT/eval_perturb/test_roi_perturb_${tag}_v1.json" ]]; then
    NEED_BUILD=1
    break
  fi
done

if [[ "$NEED_BUILD" -eq 1 ]]; then
  log "building perturbed eval datasets"
  cd "$ROOT"
  PYTHONPYCACHEPREFIX="$PYCACHE" "$CONDA_PY" python/src/build_roi_perturb_dataset.py \
    --metadata-csv "$META_CSV" \
    --data-root    "$ROOT/python/data" \
    --output-root  "$DATA_ROOT"
else
  log "perturbed datasets already exist; skipping build"
fi

# 2. Run evaluation per tier
SUMMARY_CSV="$ROOT/python/output/eval/roi_sensitivity_summary.csv"
mkdir -p "$(dirname "$SUMMARY_CSV")"
# Header (overwrite each full run)
printf "tag,samples,accuracy,precision,recall,f1,fpr,fnr,part_accuracy,finish_accuracy,unfinish_accuracy\n" \
  > "$SUMMARY_CSV"

for tag in $PERTURB_TAGS; do
  EXP_NAME="${MODEL_NAME}_roi_perturb_${tag}"
  EVAL_FILE="$DATA_ROOT/eval_perturb/test_roi_perturb_${tag}_v1.json"
  OUT_DIR="$ROOT/python/output/eval/$EXP_NAME"
  mkdir -p "$OUT_DIR"

  log "[$tag] evaluating -> $OUT_DIR"
  cd "$ROOT"
  PYTHONPYCACHEPREFIX="$PYCACHE" \
  TRANSFORMERS_NO_TF=1 USE_TF=0 \
  CUDA_VISIBLE_DEVICES="$EVAL_GPU" \
  VLM_MODEL_ID="$MODEL_DIR" \
  VLM_EVAL_EXPERIMENT_NAME="$EXP_NAME" \
  VLM_EVAL_FILES="$EVAL_FILE" \
  VLM_IMAGE_ROOT="$DATA_ROOT" \
  "$CONDA_PY" python/src/evaluate_model.py \
    > "$OUT_DIR/eval.log" 2>&1

  log "[$tag] computing metrics"
  PYTHONPYCACHEPREFIX="$PYCACHE" \
  "$CONDA_PY" python/src/compute_verification_metrics.py "$OUT_DIR" \
    >> "$OUT_DIR/eval.log" 2>&1

  # Append a row to the consolidated summary
  METRIC_JSON="$OUT_DIR/metrics_summary.csv"
  if [[ -f "$METRIC_JSON" ]]; then
    # First non-header row of metrics_summary.csv
    tail -n +2 "$METRIC_JSON" | head -n 1 | awk -v tag="$tag" -F, '{
      # metrics_summary.csv columns produced by compute_verification_metrics.py:
      # dataset,samples,accuracy,precision,recall,f1,fpr,fnr,part_accuracy,
      # finish_accuracy,unfinish_accuracy,tp,tn,fp,fn
      printf "%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n", \
        tag, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11
    }' >> "$SUMMARY_CSV"
  else
    log "[$tag] WARN: $METRIC_JSON not produced; check $OUT_DIR/eval.log"
  fi
done

log "consolidated summary -> $SUMMARY_CSV"
log "all tiers done."
