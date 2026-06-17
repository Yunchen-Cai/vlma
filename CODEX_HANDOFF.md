# Codex Handoff

## Purpose

This document is the current handoff for the VLMA ROI paper line. It records:

- what has already been validated
- what the present codebase can already run
- what the next main-paper experiment line should be
- which commands should be executed on the cloud machine
- which claims are already supported and which still require new evidence

The new main direction is no longer a single-part pilot. The target paper line is now:

1. four-part ROI-aligned completion verification
2. source-disjoint cover generalization
3. few-shot data-efficiency evidence
4. optional unified multi-task model as a supplementary systems result

## Repository Structure

### Main research code

- `python/src/`
- `python/data/`
- `python/output/`
- `python/ROI_MIXED_EXPERIMENT.md`

### Java backend

- `VideoAssemblyMonitor/`

### Frontend

- `VideoAssemblyMonitorWeb/`

The Java and frontend code are not the focus of the ROI paper experiments.

## Current Scientific Goal

The paper should now make a narrower but stronger claim:

> ROI-aligned supervision improves local completion perception in VLM-based assembly verification, especially by reducing false acceptance on visually subtle unfinished states.

The paper should avoid over-claiming broad generalization before multi-part and source-disjoint evidence are added.

## What Has Already Been Completed

### 1. Full-SFT pipeline

The cloud pipeline already supports full supervised fine-tuning from:

- `python/models/Qwen2.5-VL-7B-Instruct`

Primary training entry:

- `python/src/full_sft_train.py`

Convenience pipeline launcher:

- `python/src/run_single_pipeline.sh`

### 2. Cover ROI pilot

The first completed ROI pilot is for:

- `Port End Cover`

Existing ROI assets:

- `python/data/roi_annotations_v1.csv`
- `python/data/roi_experiment_v1/`

Existing helper scripts:

- `python/src/collect_cover_roi_input.py`
- `python/src/annotate_roi_boxes.py`
- `python/src/prepare_roi_mixed_dataset.py`
- `python/src/evaluate_model.py`
- `python/src/compute_verification_metrics.py`
- `python/src/export_loss_curve.py`
- `python/src/create_stratified_subsets.py`
- `python/src/plot_main_results.py`
- `python/src/plot_fewshot_curves.py`

### 3. Cover pilot results already validated

The cover pilot already provides strong evidence that ROI supervision improves local verification reliability.

Key observed results:

| Model | Test Full Accuracy | Test ROI Accuracy | Test ROI F1 | Test ROI FPR |
| --- | ---: | ---: | ---: | ---: |
| Base Qwen2.5-VL-7B-Instruct | 0.639 | 0.556 | 0.000 | 0.000 |
| Full-only full SFT | 1.000 | 0.972 | 0.970 | 0.050 |
| ROI-only full SFT | 1.000 | 1.000 | 1.000 | 0.000 |
| Full+ROI mixed full SFT | 1.000 | 0.991 | 0.990 | 0.0167 |

Interpretation:

- ROI supervision clearly improves local completion discrimination.
- The most safety-relevant improvement is the reduction of false acceptance on ROI-side unfinished samples.
- `ROI-only` is the cleanest mechanism proof for local perception.
- `Full+ROI mixed` remains attractive as a unified deployment model.

### 4. Few-shot pilot already validated

Few-shot pilot experiments were completed for the cover-only setting. The main takeaway is:

- ROI supervision is data-efficient on the ROI-side verification task.
- The curve is not perfectly monotonic, so future paper text should describe it as empirical evidence rather than a smooth scaling law.

## Current Data Reality

### Data already present in the repo/cloud

- `python/data/2.3vlm_status_data.json`
- `python/data/3.14vlm_verification_data.json`
- `python/data/3.16test_general_verification_data.json`
- `python/data/3.16test_guided_verification_data.json`
- `python/data/clean_assembly_sft_12.23merged.json`

### Important frame directories

The next experiment stage assumes these directories are present on the cloud machine:

- `python/data/2.3vlm_status_frames/`
- `python/data/3.14vlm_verification_frames/`
- `python/data/3.16test_vlm_verification_frames/`

### What these datasets mean

`2.3vlm_status_frames`:

- contains multiple parts
- includes at least `Port End Cover`, `Drive Gear`, `Gear Housing`, and `Thrust Block`
- is the correct source for a four-part ROI training benchmark

`3.14vlm_verification_frames`:

- should be treated as an external plain-prompt cover validation set

`3.16test_vlm_verification_frames`:

- should be treated as an external cover test set
- plain-prompt evaluation should be generated from the images directly for ROI-controlled comparison
- the original guided JSON should be used only for the prompt supplementary experiment

### Important caution

The current `roi_experiment_v1` assets contain only `Port End Cover`. They are not yet a valid four-part ROI benchmark.

## Main Experimental Strategy Going Forward

The next paper-stage experiments should be organized into four blocks.

### Block A. Four-part in-domain ROI benchmark

Purpose:

- show that ROI supervision is not only a single-part cover artifact
- extend the mechanism evidence to four parts

Training source:

- `2.3vlm_status_frames` only

Parts:

- `Port End Cover`
- `Drive Gear`
- `Gear Housing`
- `Thrust Block`

Variants:

1. `Full-only`
2. `ROI-only`
3. `Full+ROI mixed`

### Block B. Source-disjoint cover generalization benchmark

Purpose:

- address the concern that the pilot may be inflated by same-source or near-frame overlap

Recommended split:

- train: `2.3` cover only
- validation: `3.14` cover only
- test: `3.16` cover only

Prompt policy:

- keep the verification prompt identical across full-image and ROI-image conditions

Variants:

1. `Full-only`
2. `ROI-only`
3. `Full+ROI mixed`

### Block C. Prompt supplementary experiment

Purpose:

- show that the ROI gain is not merely a prompt artifact

Recommendation:

- use the best cover model from Block B
- compare plain-prompt test against guided-prompt test on the same `3.16` source

This should remain a supplementary ablation, not the main paper narrative.

### Block D. Few-shot data-efficiency experiment

Purpose:

- show that ROI supervision reaches useful verification behavior with less data

Priority:

- run this first on the source-disjoint cover benchmark
- if resources permit, repeat on the four-part benchmark

### Block E. ROI-provider sensitivity envelope

Purpose:

- close the system claim of Section 3.5 end-to-end by quantifying how robust the deployed Full+ROI mixed model is to imperfect ROIs
- support the paper's argument that any reasonable detector with sub-10 % centre / scale error suffices as the deployed ROI provider, without committing to a specific localiser

Priority:

- run once the four-part Full+ROI mixed checkpoint of Block A is available
- no new training; only re-evaluation under controlled perturbations

### Block F. Cross-part zero-shot diagnostic

Purpose:

- support the Section 5.2 limitation that completion verification, unlike part naming, does not transfer zero-shot to new parts under the proposed supervision recipe

Priority:

- supplementary; run once Block B Cover-only Full+ROI mixed checkpoint is available
- no new training; only zero-shot re-evaluation of the Cover-only model on the four-part benchmark

## Exact Cloud Commands

All commands below assume the repository root is:

```bash
cd /mnt/workspace/users/caiyunchen/vlma
```

### Stage 0. Verify raw images are present

```bash
cd /mnt/workspace/users/caiyunchen/vlma
find python/data -maxdepth 1 -type d | grep -E '2.3vlm_status_frames|3.14vlm_verification_frames|3.16test_vlm_verification_frames'
```

### Stage 1. Build four-part ROI annotation pools from `2.3`

```bash
cd /mnt/workspace/users/caiyunchen/vlma
python python/src/collect_cover_roi_input.py \
  --source python/data/2.3vlm_status_frames \
  --keyword cover \
  --output-root python/data/roi_annotation_input_v2_4part/port_end_cover \
  --execute

python python/src/collect_cover_roi_input.py \
  --source python/data/2.3vlm_status_frames \
  --keyword drive_gear \
  --output-root python/data/roi_annotation_input_v2_4part/drive_gear \
  --execute

python python/src/collect_cover_roi_input.py \
  --source python/data/2.3vlm_status_frames \
  --keyword house \
  --output-root python/data/roi_annotation_input_v2_4part/gear_housing \
  --execute

python python/src/collect_cover_roi_input.py \
  --source python/data/2.3vlm_status_frames \
  --keyword thrust \
  --output-root python/data/roi_annotation_input_v2_4part/thrust_block \
  --execute
```

### Stage 2. Annotate the four-part ROI boxes

Run these sequentially and append to one CSV:

```bash
cd /mnt/workspace/users/caiyunchen/vlma
python python/src/annotate_roi_boxes.py \
  --input-root python/data/roi_annotation_input_v2_4part/port_end_cover \
  --output-csv python/data/roi_annotations_v2_4part.csv \
  --part "Port End Cover" \
  --preview-root python/data/roi_preview_v2_4part/port_end_cover

python python/src/annotate_roi_boxes.py \
  --input-root python/data/roi_annotation_input_v2_4part/drive_gear \
  --output-csv python/data/roi_annotations_v2_4part.csv \
  --part "Drive Gear" \
  --preview-root python/data/roi_preview_v2_4part/drive_gear

python python/src/annotate_roi_boxes.py \
  --input-root python/data/roi_annotation_input_v2_4part/gear_housing \
  --output-csv python/data/roi_annotations_v2_4part.csv \
  --part "Gear Housing" \
  --preview-root python/data/roi_preview_v2_4part/gear_housing

python python/src/annotate_roi_boxes.py \
  --input-root python/data/roi_annotation_input_v2_4part/thrust_block \
  --output-csv python/data/roi_annotations_v2_4part.csv \
  --part "Thrust Block" \
  --preview-root python/data/roi_preview_v2_4part/thrust_block
```

### Stage 3. Build the four-part in-domain ROI dataset

```bash
cd /mnt/workspace/users/caiyunchen/vlma
python python/src/prepare_roi_mixed_dataset.py \
  --metadata python/data/roi_annotations_v2_4part.csv \
  --output-root python/data/roi_experiment_v2_4part \
  --margin 0.15 \
  --seed 42 \
  --train-ratio 0.70 \
  --val-ratio 0.15
```

Expected outputs:

- `python/data/roi_experiment_v2_4part/sft/full_sft_v1.json`
- `python/data/roi_experiment_v2_4part/sft/roi_only_sft_v1.json`
- `python/data/roi_experiment_v2_4part/sft/full_roi_mixed_sft_v1.json`
- `python/data/roi_experiment_v2_4part/eval/test_full_v1.json`
- `python/data/roi_experiment_v2_4part/eval/test_roi_v1.json`

### Stage 4. Run the four-part in-domain main experiments

```bash
cd /mnt/workspace/users/caiyunchen/vlma
bash python/src/run_single_pipeline.sh \
  /mnt/workspace/users/caiyunchen/vlma/python/data/roi_experiment_v2_4part/sft/full_sft_v1.json \
  fourpart_full_only_fullsft_v2 \
  4

bash python/src/run_single_pipeline.sh \
  /mnt/workspace/users/caiyunchen/vlma/python/data/roi_experiment_v2_4part/sft/roi_only_sft_v1.json \
  fourpart_roi_only_fullsft_v2 \
  4

bash python/src/run_single_pipeline.sh \
  /mnt/workspace/users/caiyunchen/vlma/python/data/roi_experiment_v2_4part/sft/full_roi_mixed_sft_v1.json \
  fourpart_full_roi_mixed_fullsft_v2 \
  4
```

### Stage 5. Build source-disjoint cover train/val/test sets

#### 5.1 Collect source-specific cover annotation pools

```bash
cd /mnt/workspace/users/caiyunchen/vlma
python python/src/collect_cover_roi_input.py \
  --source python/data/2.3vlm_status_frames \
  --keyword cover \
  --output-root python/data/roi_annotation_input_v2_cover/train_2p3 \
  --execute

python python/src/collect_cover_roi_input.py \
  --source python/data/3.14vlm_verification_frames \
  --keyword cover \
  --output-root python/data/roi_annotation_input_v2_cover/val_314 \
  --execute

python python/src/collect_cover_roi_input.py \
  --source python/data/3.16test_vlm_verification_frames \
  --keyword cover \
  --output-root python/data/roi_annotation_input_v2_cover/test_316 \
  --execute
```

#### 5.2 Annotate the source-specific cover pools

```bash
cd /mnt/workspace/users/caiyunchen/vlma
python python/src/annotate_roi_boxes.py \
  --input-root python/data/roi_annotation_input_v2_cover/train_2p3 \
  --output-csv python/data/roi_annotations_cover_train_2p3.csv \
  --part "Port End Cover" \
  --preview-root python/data/roi_preview_v2_cover/train_2p3

python python/src/annotate_roi_boxes.py \
  --input-root python/data/roi_annotation_input_v2_cover/val_314 \
  --output-csv python/data/roi_annotations_cover_val_314.csv \
  --part "Port End Cover" \
  --preview-root python/data/roi_preview_v2_cover/val_314

python python/src/annotate_roi_boxes.py \
  --input-root python/data/roi_annotation_input_v2_cover/test_316 \
  --output-csv python/data/roi_annotations_cover_test_316.csv \
  --part "Port End Cover" \
  --preview-root python/data/roi_preview_v2_cover/test_316
```

#### 5.3 Build train and external eval datasets with identical prompts

```bash
cd /mnt/workspace/users/caiyunchen/vlma
python python/src/prepare_roi_mixed_dataset.py \
  --metadata python/data/roi_annotations_cover_train_2p3.csv \
  --output-root python/data/roi_experiment_cover_train_2p3 \
  --margin 0.15 \
  --seed 42 \
  --train-ratio 1.0 \
  --val-ratio 0.0

python python/src/prepare_roi_mixed_dataset.py \
  --metadata python/data/roi_annotations_cover_val_314.csv \
  --output-root python/data/roi_experiment_cover_val_314 \
  --margin 0.15 \
  --seed 42 \
  --train-ratio 0.0 \
  --val-ratio 0.0

python python/src/prepare_roi_mixed_dataset.py \
  --metadata python/data/roi_annotations_cover_test_316.csv \
  --output-root python/data/roi_experiment_cover_test_316 \
  --margin 0.15 \
  --seed 42 \
  --train-ratio 0.0 \
  --val-ratio 0.0
```

### Stage 6. Train the source-disjoint cover models

```bash
cd /mnt/workspace/users/caiyunchen/vlma
bash python/src/run_single_pipeline.sh \
  /mnt/workspace/users/caiyunchen/vlma/python/data/roi_experiment_cover_train_2p3/sft/full_sft_v1.json \
  coverx_full_only_fullsft_v2 \
  6

bash python/src/run_single_pipeline.sh \
  /mnt/workspace/users/caiyunchen/vlma/python/data/roi_experiment_cover_train_2p3/sft/roi_only_sft_v1.json \
  coverx_roi_only_fullsft_v2 \
  6

bash python/src/run_single_pipeline.sh \
  /mnt/workspace/users/caiyunchen/vlma/python/data/roi_experiment_cover_train_2p3/sft/full_roi_mixed_sft_v1.json \
  coverx_full_roi_mixed_fullsft_v2 \
  6
```

### Stage 7. Evaluate the source-disjoint cover models on `3.14` plain prompt

Example for the mixed model:

```bash
cd /mnt/workspace/users/caiyunchen/vlma
TRANSFORMERS_NO_TF=1 USE_TF=0 CUDA_VISIBLE_DEVICES=0 \
VLM_MODEL_ID=/mnt/workspace/users/caiyunchen/vlma/python/output/coverx_full_roi_mixed_fullsft_v2 \
VLM_EVAL_EXPERIMENT_NAME=coverx_full_roi_mixed_eval_314_plain \
VLM_EVAL_FILES=/mnt/workspace/users/caiyunchen/vlma/python/data/roi_experiment_cover_val_314/eval/test_full_v1.json,/mnt/workspace/users/caiyunchen/vlma/python/data/roi_experiment_cover_val_314/eval/test_roi_v1.json \
python python/src/evaluate_model.py

python python/src/compute_verification_metrics.py \
  /mnt/workspace/users/caiyunchen/vlma/python/output/eval/coverx_full_roi_mixed_eval_314_plain
```

Repeat with:

- `coverx_full_only_fullsft_v2`
- `coverx_roi_only_fullsft_v2`
- `coverx_full_roi_mixed_fullsft_v2`

### Stage 8. Evaluate the source-disjoint cover models on `3.16` plain prompt

```bash
cd /mnt/workspace/users/caiyunchen/vlma
TRANSFORMERS_NO_TF=1 USE_TF=0 CUDA_VISIBLE_DEVICES=0 \
VLM_MODEL_ID=/mnt/workspace/users/caiyunchen/vlma/python/output/coverx_full_roi_mixed_fullsft_v2 \
VLM_EVAL_EXPERIMENT_NAME=coverx_full_roi_mixed_eval_316_plain \
VLM_EVAL_FILES=/mnt/workspace/users/caiyunchen/vlma/python/data/roi_experiment_cover_test_316/eval/test_full_v1.json,/mnt/workspace/users/caiyunchen/vlma/python/data/roi_experiment_cover_test_316/eval/test_roi_v1.json \
python python/src/evaluate_model.py

python python/src/compute_verification_metrics.py \
  /mnt/workspace/users/caiyunchen/vlma/python/output/eval/coverx_full_roi_mixed_eval_316_plain
```

### Stage 9. Guided-prompt supplementary experiment

Use the best Block B model and evaluate on the original guided JSON:

```bash
cd /mnt/workspace/users/caiyunchen/vlma
TRANSFORMERS_NO_TF=1 USE_TF=0 CUDA_VISIBLE_DEVICES=0 \
VLM_MODEL_ID=/mnt/workspace/users/caiyunchen/vlma/python/output/coverx_full_roi_mixed_fullsft_v2 \
VLM_EVAL_EXPERIMENT_NAME=coverx_full_roi_mixed_eval_316_guided \
VLM_EVAL_FILES=/mnt/workspace/users/caiyunchen/vlma/python/data/3.16test_guided_verification_data.json \
python python/src/evaluate_model.py

python python/src/compute_verification_metrics.py \
  /mnt/workspace/users/caiyunchen/vlma/python/output/eval/coverx_full_roi_mixed_eval_316_guided
```

### Stage 10. Few-shot experiment on the source-disjoint cover benchmark

Recommended subset sizes for the smaller cover-only train set:

- `25`
- `50`
- `100`
- `150`

Create subsets:

```bash
cd /mnt/workspace/users/caiyunchen/vlma
python python/src/create_stratified_subsets.py \
  python/data/roi_experiment_cover_train_2p3/sft/full_sft_v1.json \
  python/data/roi_experiment_cover_train_2p3/fewshot \
  25 50 100 150

python python/src/create_stratified_subsets.py \
  python/data/roi_experiment_cover_train_2p3/sft/roi_only_sft_v1.json \
  python/data/roi_experiment_cover_train_2p3/fewshot \
  25 50 100 150
```

Train each subset:

```bash
cd /mnt/workspace/users/caiyunchen/vlma
bash python/src/run_single_pipeline.sh \
  /mnt/workspace/users/caiyunchen/vlma/python/data/roi_experiment_cover_train_2p3/fewshot/full_sft_v1_25.json \
  coverx_full_only_fs25 \
  12

bash python/src/run_single_pipeline.sh \
  /mnt/workspace/users/caiyunchen/vlma/python/data/roi_experiment_cover_train_2p3/fewshot/roi_only_sft_v1_25.json \
  coverx_roi_only_fs25 \
  12
```

Repeat similarly for `50`, `100`, and `150`.

### Stage 11. Optional unified multi-task model

This is a supplementary systems experiment, not the main ROI perception claim.

Merge datasets:

```bash
cd /mnt/workspace/users/caiyunchen/vlma
python - <<'PY'
import json, random
from pathlib import Path

root = Path('/mnt/workspace/users/caiyunchen/vlma/python')
assembly = json.loads((root / 'data' / 'clean_assembly_sft_12.23merged.json').read_text(encoding='utf-8'))
roi = json.loads((root / 'data' / 'roi_experiment_v2_4part' / 'sft' / 'full_roi_mixed_sft_v1.json').read_text(encoding='utf-8'))
merged = assembly + roi
random.Random(42).shuffle(merged)
out_path = root / 'data' / 'multitask_assembly_plus_roi_v1.json'
out_path.write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding='utf-8')
print(f'assembly={len(assembly)} roi={len(roi)} total={len(merged)}')
print(out_path)
PY
```

Train:

```bash
cd /mnt/workspace/users/caiyunchen/vlma
bash python/src/run_single_pipeline.sh \
  /mnt/workspace/users/caiyunchen/vlma/python/data/multitask_assembly_plus_roi_v1.json \
  multitask_assembly_plus_roi_fullsft_v1 \
  4
```

Immediate verification check:

```bash
cd /mnt/workspace/users/caiyunchen/vlma
TRANSFORMERS_NO_TF=1 USE_TF=0 CUDA_VISIBLE_DEVICES=0 \
VLM_MODEL_ID=/mnt/workspace/users/caiyunchen/vlma/python/output/multitask_assembly_plus_roi_fullsft_v1 \
VLM_EVAL_EXPERIMENT_NAME=multitask_assembly_plus_roi_verification_eval \
VLM_EVAL_FILES=/mnt/workspace/users/caiyunchen/vlma/python/data/roi_experiment_cover_test_316/eval/test_full_v1.json,/mnt/workspace/users/caiyunchen/vlma/python/data/roi_experiment_cover_test_316/eval/test_roi_v1.json \
python python/src/evaluate_model.py
```

### Stage 12. ROI-provider sensitivity evaluation

This stage produces the perturbation envelope reported in §4.3.2 of the paper (Table 7 / Fig. 10). It does not require new training: the best four-part `Full+ROI mixed` checkpoint from Stage 4 is re-evaluated under deterministic ROI perturbations.

Five perturbation tiers are applied to the four-part GT ROIs:

- `c5`, `c10`, `c15` — centre offset of ±5 / ±10 / ±15 % of ROI side length
- `s10`, `s20` — scale jitter of ±10 / ±20 %

Run end-to-end:

```bash
cd /mnt/workspace/users/caiyunchen/vlma
bash python/src/run_roi_sensitivity_eval.sh
```

Override defaults if needed:

```bash
EVAL_GPU=0 \
PERTURB_TAGS="c5 c10 c15 s10 s20" \
MODEL_NAME=fourpart_full_roi_mixed_fullsft_v2_rerun \
bash python/src/run_roi_sensitivity_eval.sh
```

The script:

1. invokes `build_roi_perturb_dataset.py` to materialise the perturbed crops and matching eval JSONs;
2. runs `evaluate_model.py` against the Full+ROI mixed checkpoint on each tier;
3. runs `compute_verification_metrics.py` to produce per-tier `metrics_summary.csv`;
4. emits a consolidated `roi_sensitivity_summary.csv`.

The Full-only baseline of Stage 4 is included as the lower-bound reference. Reproduce-on-demand: perturbations are seeded by image basename, so reruns produce bit-identical crops.

Outputs land in:

- `python/data/roi_experiment_v2_4part/eval_perturb/test_roi_perturb_<tag>_v1.json`
- `python/data/roi_experiment_v2_4part/images_roi_bbox_perturb/<tag>/<part_dir>/<basename>_perturb_<tag>.jpg`
- `python/output/<MODEL_NAME>/.../roi_sensitivity_summary.csv`

### Stage 13. Cross-part zero-shot diagnostic

This is a supplementary diagnostic that supports the limitation reported in §5.2(iv) and Appendix C / Table C.1 of the paper. It does not require new training: the Cover-only `Full+ROI mixed` checkpoint from Stage 6 is re-evaluated zero-shot on the four-part held-out test set from Stage 3.

```bash
cd /mnt/workspace/users/caiyunchen/vlma
TRANSFORMERS_NO_TF=1 USE_TF=0 CUDA_VISIBLE_DEVICES=0 \
VLM_MODEL_ID=/mnt/workspace/users/caiyunchen/vlma/python/output/coverx_full_roi_mixed_fullsft_v2 \
VLM_EVAL_EXPERIMENT_NAME=coverx_full_roi_mixed_on_fourpart_zero_shot \
VLM_EVAL_FILES=/mnt/workspace/users/caiyunchen/vlma/python/data/roi_experiment_v2_4part/eval/test_full_v1.json,/mnt/workspace/users/caiyunchen/vlma/python/data/roi_experiment_v2_4part/eval/test_roi_v1.json \
python python/src/evaluate_model.py
```

The downstream metric expected by the paper is the per-part confusion table (`Port End Cover`, `Drive Gear`, `Gear Housing`, `Thrust Block`), aggregated by `compute_verification_metrics.py` from the per-sample `part` field of the predicted JSONs. The expected pattern is perfect part-name recognition on all 224 frames but a degenerate "Unfinish-by-default" response on the three unseen parts, yielding 0 / 38 correctly recovered unseen-part `Finish` frames. This justifies the §5.2 conclusion that completion verification, unlike part naming, does not transfer zero-shot to new parts under the proposed supervision recipe.

## Expected Output Directories

Main output roots:

- `python/output/fourpart_full_only_fullsft_v2/`
- `python/output/fourpart_roi_only_fullsft_v2/`
- `python/output/fourpart_full_roi_mixed_fullsft_v2/`
- `python/output/coverx_full_only_fullsft_v2/`
- `python/output/coverx_roi_only_fullsft_v2/`
- `python/output/coverx_full_roi_mixed_fullsft_v2/`

Main evaluation roots:

- `python/output/eval/fourpart_full_only_fullsft_v2_eval/`
- `python/output/eval/fourpart_roi_only_fullsft_v2_eval/`
- `python/output/eval/fourpart_full_roi_mixed_fullsft_v2_eval/`
- `python/output/eval/coverx_full_only_eval_314_plain/`
- `python/output/eval/coverx_roi_only_eval_314_plain/`
- `python/output/eval/coverx_full_roi_mixed_eval_314_plain/`
- `python/output/eval/coverx_full_only_eval_316_plain/`
- `python/output/eval/coverx_roi_only_eval_316_plain/`
- `python/output/eval/coverx_full_roi_mixed_eval_316_plain/`

## Recommended Paper Framing

### Primary claim

ROI-aligned supervision improves local completion verification and reduces false acceptance on subtle unfinished states.

### Secondary claim

The benefit is not limited to a single part once the benchmark is expanded to multiple parts.

### Supplementary claim

Prompt engineering can help, but it does not replace ROI-aligned visual supervision.

### Deployment claim

`Full+ROI mixed` is the most natural unified deployment model when the system must support both global assembly understanding and local completion verification.

## Current Highest-Priority Remaining Risks

1. The four-part benchmark still needs new ROI annotations.
2. The strongest source-disjoint evidence is still cover-centric unless new external sets are collected for the other three parts.
3. Multi-task regression on the legacy action/tool/part task still needs a cleaned evaluation entry if that result is to be used in the paper.
