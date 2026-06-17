# Four-Part ROI-Aligned Completion Verification

## Main-Paper Experimental Protocol

## 1. Research Objective

This document defines the main experimental protocol for the next paper-stage ROI study in the VLMA repository. The objective is no longer a single-part pilot. The target evidence chain is now:

1. a four-part ROI verification benchmark
2. a source-disjoint cover generalization benchmark
3. a few-shot data-efficiency study
4. an optional unified multi-task model as a supplementary systems result

The central scientific question is:

> Does ROI-aligned supervision improve the visual-language model's sensitivity to fine-grained assembly completion cues, or are the observed gains primarily caused by prompt bias or narrow single-part overfitting?

## 2. Working Claim for the Paper

The paper should make a focused primary claim:

> ROI-aligned supervision improves local completion perception in assembly verification, especially by reducing false acceptance on visually subtle unfinished states.

This claim is stronger and more defensible than a broad statement about universal assembly generalization.

## 3. Hypotheses

### H1. ROI supervision improves local completion verification

Compared with full-image-only training, ROI-aligned training should improve verification performance on ROI-view evaluation, especially on hard unfinished cases.

### H2. The gain is not merely a prompt artifact

Under matched prompts, ROI-trained models should still outperform full-image-only models. Guided prompts may help further, but they should not fully explain the gain.

### H3. The gain extends beyond a single target part

A four-part benchmark should show that ROI supervision is not only a `Port End Cover` phenomenon.

### H4. ROI supervision is data-efficient

At small training sizes, ROI-aligned training should reach stronger ROI-side verification performance than full-image-only training.

## 4. Why the Previous Cover Pilot Matters

The completed cover pilot already showed the right mechanism:

| Model | Test Full Accuracy | Test ROI Accuracy | Test ROI F1 | Test ROI FPR |
| --- | ---: | ---: | ---: | ---: |
| Base Qwen2.5-VL-7B-Instruct | 0.639 | 0.556 | 0.000 | 0.000 |
| Full-only full SFT | 1.000 | 0.972 | 0.970 | 0.050 |
| ROI-only full SFT | 1.000 | 1.000 | 1.000 | 0.000 |
| Full+ROI mixed full SFT | 1.000 | 0.991 | 0.990 | 0.0167 |

The most important interpretation is not the raw accuracy gain. It is the reduction of false acceptance on unfinished ROI-side samples.

This pilot should be described in the paper as:

- a completed mechanism proof
- a motivation for the four-part extension
- preliminary evidence that local supervision changes what the model attends to

## 5. Dataset Design

## 5.1 Dataset roles

### `2.3vlm_status_frames`

Role:

- four-part ROI training benchmark
- in-domain internal split

Parts confirmed in the source:

- `Port End Cover`
- `Drive Gear`
- `Gear Housing`
- `Thrust Block`

### `3.14vlm_verification_frames`

Role:

- external plain-prompt cover validation set

### `3.16test_vlm_verification_frames`

Role:

- external plain-prompt cover test set
- same-image source for guided-prompt supplementary evaluation

### `3.16test_guided_verification_data.json`

Role:

- supplementary prompt experiment only
- not part of the main matched-prompt ROI comparison

## 5.2 Benchmark split logic

The paper should use two complementary benchmarks rather than forcing one dataset design to answer every question.

### Benchmark A: Four-part in-domain ROI benchmark

Purpose:

- demonstrate that ROI supervision extends beyond a single part

Source:

- `2.3vlm_status_frames` only

Split:

- internal stratified train/val/test split
- stratify by `part`, `gt_verification`, and `hard_case`

### Benchmark B: Source-disjoint cover generalization benchmark

Purpose:

- address the concern that the original pilot may be inflated by same-source overlap

Recommended source split:

- train: `2.3` cover only
- validation: `3.14` cover only
- test: `3.16` cover only

Prompt policy:

- keep the evaluation prompt identical across full-image and ROI-image conditions

This benchmark is the cleanest answer to the question:

> If the test source changes, does ROI supervision still help?

## 6. Experimental Matrix

## 6.1 Primary model variants

Every main-paper comparison should use:

- the same base model
- the same full-SFT regime
- the same output format

Base model:

- `Qwen2.5-VL-7B-Instruct`

Training regime:

- full supervised fine-tuning

Variants:

1. `Full-only`
2. `ROI-only`
3. `Full+ROI mixed`

## 6.2 What each variant means

### Full-only

Input:

- full-frame image only

Purpose:

- baseline model with global context but no explicit ROI supervision

### ROI-only

Input:

- ROI crop only

Purpose:

- upper-bound mechanism test for local completion discrimination

### Full+ROI mixed

Input:

- independent single-image full-frame and ROI samples with the same label

Purpose:

- unified training regime that preserves global context while explicitly teaching local completion cues

## 6.3 Main comparisons

### Benchmark A: four-part in-domain benchmark

Train:

- `Full-only`
- `ROI-only`
- `Full+ROI mixed`

Evaluate:

- `test_full_v1.json`
- `test_roi_v1.json`

Questions answered:

- does ROI help across four parts?
- is mixed training sufficient to preserve global context while improving local verification?

### Benchmark B: source-disjoint cover benchmark

Train:

- `Full-only`
- `ROI-only`
- `Full+ROI mixed`

Evaluate on plain prompt:

- `3.14` full-image test
- `3.14` ROI-image test
- `3.16` full-image test
- `3.16` ROI-image test

Questions answered:

- does ROI help when the source changes?
- does the ROI gain survive under matched prompts?

### Supplementary prompt experiment

Evaluate:

- best model from Benchmark B on `3.16test_guided_verification_data.json`

Question answered:

- how much additional performance comes from guided prompting after the model has already learned ROI-sensitive visual cues?

## 7. Metrics

Use `Finish` as the positive class.

Report:

- Accuracy
- Precision
- Recall
- F1-score
- False Positive Rate
- False Negative Rate
- Finish accuracy
- Unfinish accuracy
- Part accuracy

The most important safety metric is:

- false acceptance rate

Operational definition:

- `GT = Unfinish`, `Pred = Finish`

In assembly verification, this error is usually more dangerous than conservative rejection.

## 8. Expected Paper Story

## 8.1 Primary story

The main story should be:

1. The cover pilot already shows that ROI supervision reduces false acceptance.
2. The four-part benchmark shows that the effect is not unique to a single component.
3. The source-disjoint cover benchmark shows that the gain is not only a same-source artifact.
4. The few-shot benchmark shows that ROI supervision is data-efficient.

## 8.2 Supplementary story

The supplementary story should be:

1. Guided prompts help, but do not replace ROI supervision.
2. `Full+ROI mixed` is the most practical unified deployment variant.
3. A unified multi-task model is possible, but it is a systems result rather than the main scientific claim.

## 9. Exact Cloud Commands

All commands below assume:

```bash
cd /mnt/workspace/users/caiyunchen/vlma
```

## 9.1 Verify the required frame directories

```bash
cd /mnt/workspace/users/caiyunchen/vlma
find python/data -maxdepth 1 -type d | grep -E '2.3vlm_status_frames|3.14vlm_verification_frames|3.16test_vlm_verification_frames'
```

## 9.2 Build four-part ROI annotation pools from `2.3`

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

## 9.3 Annotate the four-part ROI boxes

Append all parts into one CSV:

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

## 9.4 Build the four-part in-domain ROI dataset

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

## 9.5 Train the four-part in-domain benchmark

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

## 9.6 Build the source-disjoint cover benchmark

### Step 1: collect source-specific cover pools

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

### Step 2: annotate the source-specific cover pools

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

### Step 3: generate prompt-controlled train and eval JSONs

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

## 9.7 Train the source-disjoint cover benchmark

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

## 9.8 Evaluate on `3.14` plain prompt

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

Repeat for:

- `coverx_full_only_fullsft_v2`
- `coverx_roi_only_fullsft_v2`
- `coverx_full_roi_mixed_fullsft_v2`

## 9.9 Evaluate on `3.16` plain prompt

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

## 9.10 Guided-prompt supplementary evaluation

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

Interpretation rule:

- use this as a prompt supplementary result
- do not mix it into the main matched-prompt ROI table

## 9.11 Few-shot data-efficiency study

The source-disjoint cover benchmark is the preferred few-shot setting because it is more convincing than a same-source split.

Recommended subset sizes:

- `25`
- `50`
- `100`
- `150`

Generate subsets:

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

Recommended epochs:

- `25`: 12 epochs
- `50`: 12 epochs
- `100`: 8 epochs
- `150`: 6 epochs

Example:

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

Repeat for `50`, `100`, and `150`.

## 9.12 Optional unified multi-task model

This is a supplementary systems experiment. It should not replace the main ROI perception line.

Merge the multi-task dataset:

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

Immediate verification regression check:

```bash
cd /mnt/workspace/users/caiyunchen/vlma
TRANSFORMERS_NO_TF=1 USE_TF=0 CUDA_VISIBLE_DEVICES=0 \
VLM_MODEL_ID=/mnt/workspace/users/caiyunchen/vlma/python/output/multitask_assembly_plus_roi_fullsft_v1 \
VLM_EVAL_EXPERIMENT_NAME=multitask_assembly_plus_roi_verification_eval \
VLM_EVAL_FILES=/mnt/workspace/users/caiyunchen/vlma/python/data/roi_experiment_cover_test_316/eval/test_full_v1.json,/mnt/workspace/users/caiyunchen/vlma/python/data/roi_experiment_cover_test_316/eval/test_roi_v1.json \
python python/src/evaluate_model.py
```

## 9.13 ROI-provider sensitivity evaluation

This experiment quantifies how robust the deployed Full+ROI mixed model is to imperfect ROIs. It corresponds to the sensitivity analysis reported in §4.3.2 of the paper (Table 7 / Fig. 10). The motivation is that any real ROI provider — whether a small detector, an open-vocabulary localiser, or a fixed-camera lookup table — will produce bounding boxes that deviate from the ground truth by a few percent. Reporting an envelope under bounded perturbation lets the system claim be closed end-to-end without committing to a specific detector.

Two families of perturbations are applied to the four-part ground-truth ROIs (`roi_experiment_v2_4part/metadata/split_test_v1.csv`):

- **Centre offset**: ROI centre shifted by a fraction `δ_c` of the ROI side length, with `δ_c ∈ {±5 %, ±10 %, ±15 %}` and direction sampled uniformly per sample.
- **Scale jitter**: ROI side length rescaled by `1 + δ_s`, with `δ_s ∈ {±10 %, ±20 %}`.

The five perturbation tiers (`c5 c10 c15 s10 s20`) are sampled with a per-sample-deterministic RNG (seeded by image basename), so the perturbed test sets are bit-identical across reruns.

Build the perturbed eval datasets and run evaluation on each tier:

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

1. invokes `build_roi_perturb_dataset.py` to generate the perturbed crops and the matching SFT-style eval JSONs;
2. runs `evaluate_model.py` against the Full+ROI mixed checkpoint on each tier;
3. runs `compute_verification_metrics.py` to produce per-tier `metrics_summary.csv`;
4. emits a consolidated `roi_sensitivity_summary.csv` across all tiers.

The expected output is verification Accuracy / FPR / Unfinish-accuracy per tier, with the Full-only baseline included as the lower-bound reference. The paper's headline claim is that the worst-observed FPR across the full ± 5–± 15 % centre-offset / ± 10–± 20 % scale-jitter envelope remains an order of magnitude below the Full-only baseline (60.23 %), supporting the system claim that any reasonable deployed ROI provider with sub-10 % centre / scale error suffices.

Outputs land in:

- `python/data/roi_experiment_v2_4part/eval_perturb/test_roi_perturb_<tag>_v1.json`
- `python/data/roi_experiment_v2_4part/images_roi_bbox_perturb/<tag>/<part_dir>/<basename>_perturb_<tag>.jpg`
- `python/output/<MODEL_NAME>/.../roi_sensitivity_summary.csv`

## 9.14 Cross-part zero-shot transfer evaluation

This is a supplementary diagnostic experiment that motivates the limitation reported in §5.2(iv) of the paper (Appendix C, Table C.1). It tests whether a Full+ROI mixed model trained only on `Port End Cover` data generalises zero-shot to the other three parts (`Drive Gear`, `Gear Housing`, `Thrust Block`).

No new training is required. The Cover-only Full+ROI mixed checkpoint from §9.7 (Benchmark B) is re-evaluated on the four-part held-out test set used in §9.5 (Benchmark A), with neither the General-mode nor the Verification-mode prompts being re-conditioned on the new parts.

```bash
cd /mnt/workspace/users/caiyunchen/vlma
TRANSFORMERS_NO_TF=1 USE_TF=0 CUDA_VISIBLE_DEVICES=0 \
VLM_MODEL_ID=/mnt/workspace/users/caiyunchen/vlma/python/output/cover_only_full_roi_mixed_fullsft_v1 \
VLM_EVAL_EXPERIMENT_NAME=cover_only_on_fourpart_zero_shot \
VLM_EVAL_FILES=/mnt/workspace/users/caiyunchen/vlma/python/data/roi_experiment_v2_4part/eval/test_full_v1.json,/mnt/workspace/users/caiyunchen/vlma/python/data/roi_experiment_v2_4part/eval/test_roi_v1.json \
python python/src/evaluate_model.py
```

The expected result, reported in Appendix C of the paper, is that the model retains perfect part-name recognition (224 / 224 frames) and perfect performance on the in-distribution Port End Cover slice (31 / 31 frames; 13 Finish + 18 Unfinish, all correct), but on the three unseen parts every Finish frame is predicted as Unfinish (0 / 38 unseen-part Finish frames correct). The aggregate apparent FPR of 0 % is therefore not evidence of safe conservative behaviour; it reflects a degenerate "Unfinish-by-default" response on unseen parts and motivates the conclusion that completion verification, unlike part naming, requires at least one labelled Finish / Unfinish example per part with the proposed supervision recipe.

The per-part confusion counts are aggregated by `compute_verification_metrics.py` when the per-part `part` field is present in the predicted JSON; the resulting table is the source of Appendix C Table C.1.

## 10. Recommended Tables

### Table 1. Cover pilot summary

Purpose:

- motivate the four-part extension

### Table 2. Four-part in-domain benchmark

Rows:

- `Full-only`
- `ROI-only`
- `Full+ROI mixed`

Columns:

- `Test Full Accuracy`
- `Test ROI Accuracy`
- `F1`
- `FPR`
- `FNR`

### Table 3. Source-disjoint cover benchmark

Rows:

- `Full-only`
- `ROI-only`
- `Full+ROI mixed`

Columns:

- `3.14 Full`
- `3.14 ROI`
- `3.16 Full`
- `3.16 ROI`
- `FPR`

### Table 4. Few-shot data efficiency

Rows:

- `25`
- `50`
- `100`
- `150`

Columns:

- `Full-only ROI-test F1`
- `ROI-only ROI-test F1`
- `Full-only ROI-test FPR`
- `ROI-only ROI-test FPR`

### Table 5. Prompt supplementary result

Rows:

- best plain-prompt model

Columns:

- `3.16 Plain`
- `3.16 Guided`

### Table 6. ROI-provider sensitivity envelope

Rows (perturbation tier):

- `GT ROI` (no perturbation)
- `c5`, `c10`, `c15` (centre offset ±5 / ±10 / ±15 %)
- `s10`, `s20` (scale jitter ±10 / ±20 %)
- `Full-only` (no ROI; lower-bound reference)

Columns:

- Accuracy
- FPR
- Unfinish accuracy

### Table 7. Cross-part zero-shot per-part breakdown

Rows (per part):

- `Port End Cover` (in-distribution)
- `Drive Gear` (unseen)
- `Gear Housing` (unseen)
- `Thrust Block` (unseen)
- `Aggregate`

Columns:

- `GT Finish predicted Finish`
- `GT Finish predicted Unfinish`
- `GT Unfinish predicted Unfinish`
- `GT Unfinish predicted Finish`

## 11. Recommended Figures

### Figure 1. Main result bar chart

Compare:

- `Full-only`
- `ROI-only`
- `Full+ROI mixed`

Metrics:

- Accuracy
- F1
- FPR

### Figure 2. Few-shot curve

Axes:

- x-axis: training samples
- y-axis: ROI-test F1

Secondary panel:

- ROI-test FPR

### Figure 3. Hard-case visualization

Show:

- unfinished examples that fooled the full-image model
- corrected predictions from the ROI-trained model

### Figure 4. ROI-provider sensitivity envelope

Plot Accuracy and FPR as a function of perturbation magnitude across the five tiers, with the Full-only lower bound overlaid as a horizontal reference line. Source: `roi_sensitivity_summary.csv` produced by §9.13.

## 12. Writing Guidance for the Paper

## 12.1 What to emphasize

- false acceptance reduction
- local completion perception
- multi-part extension
- source-disjoint cover generalization
- data efficiency

## 12.2 What not to over-claim

- do not claim universal assembly generalization
- do not claim that prompt engineering is unimportant
- do not claim that four parts are sufficient to solve all assembly perception

## 12.3 Recommended phrasing

Use language such as:

> The proposed ROI-aligned supervision strategy consistently improved local completion verification, with the strongest gains appearing in unfinished cases that were visually close to successful assembly.

Use language such as:

> ROI-only training provides the clearest evidence that explicit local supervision changes the model's perception of completion cues, whereas Full+ROI mixed training offers a more practical unified model for deployment.

## 13. Practical Notes

1. `prepare_roi_mixed_dataset.py` currently keeps the output filenames as `*_v1.json` even when used for the new v2 experiments. This is acceptable if the output root is versioned clearly.
2. The guided `3.16` JSON should not be mixed into the main matched-prompt ROI comparison.
3. The optional multi-task experiment is useful for the system story, but it is not necessary to prove the main ROI perception claim.
