# Full+ROI Mixed Fine-Tuning Experiment Plan

## Purpose

This experiment is designed to test whether a vision-language model (VLM) can improve its sensitivity to fine-grained assembly completion cues when local regions of interest (ROIs) are explicitly included in the training distribution.

The main research question is:

> Does ROI-aligned training improve the VLM's ability to distinguish true completion from visually similar incomplete states, or does performance mainly come from prompt-induced bias?

The experiment focuses on feature perception before adding stronger process-level constraints such as a finite state machine (FSM).

## Training Strategy

For the new main paper experiments, the preferred strategy is no longer LoRA or low-bit compressed fine-tuning. The user now has access to `8 x H200` GPUs, so the main ROI experiment line should be trained as full supervised fine-tuning (full SFT) from the `Qwen2.5-VL-7B-Instruct` base model.

This change is important for three reasons:

```text
The training distribution is cleaner and more consistent.
The experimental definition is easier to explain in a paper.
The results are not confounded by older LoRA-specific or quantization-specific choices.
```

Therefore:

```text
Main paper experiments:
  full SFT from Qwen2.5-VL-7B-Instruct

Legacy experiments:
  older LoRA checkpoints kept only for comparison, reference, or reproduction
```

## Core Hypothesis

Full-image training teaches the model global assembly context, but it may not reliably attend to small local cues such as hole alignment, edge gaps, gear seating, or tool-part contact. ROI samples expose these cues at a larger visual scale and reduce background distraction.

The expected outcome is that Full+ROI mixed single-image fine-tuning improves completion verification, especially on near-finished negative samples.

## Experiment Name

Recommended experiment family:

```text
roi_mixed_verification_v1
```

Recommended sub-experiments:

```text
roi_full_baseline_v1
roi_fixed_inference_only_v1
roi_bbox_inference_only_v1
roi_only_finetune_v1
roi_mixed_full_roi_finetune_v1
```

Recommended output directories:

```text
python/output/roi_full_baseline_v1/
python/output/roi_fixed_inference_only_v1/
python/output/roi_bbox_inference_only_v1/
python/output/roi_only_finetune_v1/
python/output/roi_mixed_full_roi_finetune_v1/
```

## Data Needed

### Required Raw Data

1. Original full-frame assembly images.
2. Finish/Unfinish labels for each image.
3. Part name for each image.
4. Optional but strongly recommended: hard-case category.
5. ROI annotation for at least the selected target parts.

### Minimum Recommended Dataset

Start with one part first:

```text
Port End Cover
```

Recommended minimum:

```text
Finish: 100-150 images
Clearly Unfinish: 100-150 images
Near-finished Unfinish: 100-150 images
```

If time allows, add:

```text
Drive Gear
```

### Required Metadata Fields

Create a metadata CSV with the following fields:

```csv
image_path,part,gt_verification,hard_case,x1,y1,x2,y2,roi_type,notes
```

Field definitions:

```text
image_path: path relative to python/data
part: part name, e.g. Port End Cover
gt_verification: Finish or Unfinish
hard_case: Finish, Clearly_Unfinish, Near_Finished_Unfinish, Occlusion, Illumination, etc.
x1,y1,x2,y2: bounding box coordinates in the original image
roi_type: fixed or bbox
notes: optional criterion notes
```

Example:

```csv
temp_frames/cover_correct_f33.jpg,Port End Cover,Finish,Finish,420,190,870,620,bbox,"clear corner holes; even overhang"
temp_frames/cover_wrong_f44.jpg,Port End Cover,Unfinish,Near_Finished_Unfinish,420,190,870,620,bbox,"slight hole misalignment"
```

## File Organization

Recommended directory layout:

```text
python/data/
  roi_experiment/
    metadata/
      roi_annotations_v1.csv
      split_train_v1.csv
      split_val_v1.csv
      split_test_v1.csv
    images_full/
      ...
    images_roi_fixed/
      ...
    images_roi_bbox/
      ...
    sft/
      full_sft_v1.json
      roi_only_sft_v1.json
      full_roi_mixed_sft_v1.json
    eval/
      test_full_v1.json
      test_roi_fixed_v1.json
      test_roi_bbox_v1.json
```

If the original images already live elsewhere under `python/data`, keep them there and store only generated ROI crops under:

```text
python/data/roi_experiment/images_roi_fixed/
python/data/roi_experiment/images_roi_bbox/
```

### Annotation Intake Folders

For the first pilot experiment, manually select images and place them into:

```text
python/data/roi_annotation_input/
  Finish/
  Unfinish/
```

Recommended target size for `Port End Cover`:

```text
Finish: 100-150 images
Unfinish: 100-300 images
```

The two folders provide the binary verification label. If hard-case analysis is needed later, `Unfinish` can be split or annotated into `Clearly_Unfinish` and `Near_Finished_Unfinish`.

If the cover images already exist in previous experiment folders, collect them with:

```bash
python python/src/collect_cover_roi_input.py
```

The command above is a dry run. If the summary looks correct, copy files with:

```bash
python python/src/collect_cover_roi_input.py --execute
```

The script searches the default source folders:

```text
python/data/2.3vlm_status_frames
python/data/3.14vlm_verification_frames
python/data/3.16test_vlm_verification_frames
```

Only filenames containing `cover` are considered. Images with names containing `correct`, `finish`, `finished`, `perfect`, or `ok` are copied to `Finish`; images with names containing `incorrect`, `wrong`, `unfinish`, `unfinished`, `misalign`, `upside`, `bad`, `error`, `fault`, `fail`, or `ng` are copied to `Unfinish`. Files with uncertain names are skipped and printed for manual review.

## ROI Construction

### Fixed ROI

Use this first if the camera and workstation are stable.

Definition:

```text
One manually chosen crop region per part or per camera view.
```

Example:

```text
Port End Cover fixed ROI: x1=400, y1=170, x2=900, y2=650
```

Advantages:

```text
Fast to build
No detector required
Good for testing whether local visual focus helps
```

Limitations:

```text
Less robust to camera motion or part position changes
May include irrelevant area if object shifts
```

### BBox-Based ROI

Use this after fixed ROI shows potential.

Definition:

```text
Each image has a bounding box around the target part or tool-part contact area.
```

Recommended crop rule:

```text
Expand the bounding box by 10-20 percent before cropping.
```

Reason:

```text
The VLM needs local context around the part, not only the exact object pixels.
For Port End Cover, the crop should include both the cover and the base/housing edge.
```

## Sample Construction

The current training script expects each sample to contain:

```json
{
  "image": ["relative/path/to/image.jpg"],
  "conversations": [
    {
      "role": "user",
      "content": [
        {"type": "image", "image": "relative/path/to/image.jpg"},
        {"type": "text", "text": "prompt text"}
      ]
    },
    {
      "role": "assistant",
      "content": "{\"action\": \"...\", \"tool\": \"...\", \"part\": \"...\", \"phase\": \"...\"}"
    }
  ]
}
```

For ROI verification, use a structured target focused on completion:

```json
{
  "verification": "Finish",
  "part": "Port End Cover",
  "evidence": "The four corner holes are clear and concentric, and the cover margin is even."
}
```

or, for stricter parsing:

```json
{
  "part": "Port End Cover",
  "verification": "Finish"
}
```

Use the stricter version for metric evaluation and the evidence version for qualitative reasoning experiments.

## Full+ROI Mixed Single-Image Format

The recommended mixed dataset does not require multi-image training.

For each original labeled image, create two independent single-image samples:

1. Full image sample.
2. ROI image sample.

Both samples use the same label. The prompt includes whether the image is full-frame or ROI, but keeps the task format stable.

### Full Image Sample

```json
{
  "image": ["temp_frames/cover_correct_f33.jpg"],
  "conversations": [
    {
      "role": "user",
      "content": [
        {"type": "image", "image": "temp_frames/cover_correct_f33.jpg"},
        {"type": "text", "text": "You are an assembly quality inspector. Determine whether the Port End Cover assembly state is Finish or Unfinish. Output only JSON: {\"part\": \"...\", \"verification\": \"Finish/Unfinish\"}."}
      ]
    },
    {
      "role": "assistant",
      "content": "{\"part\": \"Port End Cover\", \"verification\": \"Finish\"}"
    }
  ]
}
```

### ROI Image Sample

```json
{
  "image": ["roi_experiment/images_roi_bbox/cover_correct_f33_roi.jpg"],
  "conversations": [
    {
      "role": "user",
      "content": [
        {"type": "image", "image": "roi_experiment/images_roi_bbox/cover_correct_f33_roi.jpg"},
        {"type": "text", "text": "You are an assembly quality inspector. This image is a cropped region around the Port End Cover. Determine whether the assembly state is Finish or Unfinish. Output only JSON: {\"part\": \"...\", \"verification\": \"Finish/Unfinish\"}."}
      ]
    },
    {
      "role": "assistant",
      "content": "{\"part\": \"Port End Cover\", \"verification\": \"Finish\"}"
    }
  ]
}
```

## Dataset Variants

### Variant 1: Full-Only

File:

```text
python/data/roi_experiment/sft/full_sft_v1.json
```

Content:

```text
Only full-frame samples.
```

Purpose:

```text
Baseline for current training distribution.
```

### Variant 2: ROI-Only

File:

```text
python/data/roi_experiment/sft/roi_only_sft_v1.json
```

Content:

```text
Only ROI crop samples.
```

Purpose:

```text
Tests the upper bound of local feature aligned training.
```

### Variant 3: Full+ROI Mixed

File:

```text
python/data/roi_experiment/sft/full_roi_mixed_sft_v1.json
```

Content:

```text
Both full-frame and ROI crop samples.
Each original image contributes one full sample and one ROI sample.
```

Purpose:

```text
Tests whether the model can preserve global context while learning local completion cues.
```

### Main Training Recommendation

For the publishable ROI line, these three dataset variants should all be trained from the same `Qwen2.5-VL-7B-Instruct` initialization with full SFT:

```text
Full-only
ROI-only
Full+ROI mixed
```

Avoid mixing these new paper results with earlier LoRA-based experiments when reporting the main claims. The old LoRA runs may still be cited as preliminary baselines or engineering pilots, but the new core tables and figures should come from the unified full-SFT setup.

## Evaluation Sets

Use separate evaluation files:

```text
python/data/roi_experiment/eval/test_full_v1.json
python/data/roi_experiment/eval/test_roi_fixed_v1.json
python/data/roi_experiment/eval/test_roi_bbox_v1.json
```

Recommended evaluation matrix:

```text
Train Full -> Test Full
Train Full -> Test Fixed ROI
Train Full -> Test BBox ROI
Train ROI-only -> Test ROI
Train Full+ROI Mixed -> Test Full
Train Full+ROI Mixed -> Test ROI
```

This matrix separates two questions:

```text
Does ROI help at inference time?
Does ROI-aligned fine-tuning help the model actually learn local completion cues?
```

## Metrics

Use Finish as the positive class.

Required metrics:

```text
Accuracy
Precision
Recall
F1-score
False Positive Rate
False Negative Rate
Completion Judgment Accuracy
```

For the hard negative subset, report:

```text
Near-finished Unfinish recall
Near-finished Unfinish false acceptance rate
```

False acceptance means:

```text
GT = Unfinish, Pred = Finish
```

## Tables for the Paper

### Table A: ROI Input Comparison

```text
Full Image
Fixed ROI
BBox ROI
```

Purpose:

```text
Shows whether local visual focus improves verification.
```

### Table B: ROI-Aligned Fine-Tuning Comparison

```text
Full-only training
ROI-only training
Full+ROI mixed training
```

Purpose:

```text
Shows whether training distribution alignment is necessary.
```

### Table C: Hard Negative Analysis

```text
Clearly Unfinish
Near-finished Unfinish
Finish
```

Purpose:

```text
Shows whether the method improves subtle feature discrimination.
```

## Expected Interpretation

If ROI improves performance only during inference, the evidence suggests that local visual focus is helpful but not fully learned by the model.

If ROI-only or Full+ROI mixed fine-tuning improves F1 and reduces false acceptance on Near-finished Unfinish samples, the evidence supports the claim that ROI-aligned data improves the VLM's sensitivity to assembly completion cues.

If Full+ROI mixed training performs well on both full images and ROI images, it should be used as the main method because it preserves global context and improves local feature perception.

## Paper-Ready Wording

The ROI experiment can be described as follows:

> To distinguish genuine visual feature learning from prompt-induced response bias, we introduce a region-focused training and evaluation protocol. In addition to full-frame samples, task-relevant regions around the target assembly part are cropped and used as ROI samples. We construct a Full+ROI mixed fine-tuning set in which each original training image contributes both a full-frame sample and a corresponding ROI sample. Since all samples remain single-image inputs, the format remains compatible with the original VLM fine-tuning pipeline while exposing local completion cues at a larger visual scale.

Expected result wording:

> The Full+ROI mixed model improves verification F1-score and reduces false acceptance on near-finished incomplete samples, indicating that the gain is not merely caused by prompt bias. Instead, ROI-aligned supervision improves the model's sensitivity to local completion cues such as hole alignment, edge gaps, and part seating.

## Preparation Checklist

1. Choose target part for pilot experiment: Port End Cover.
2. Select balanced image subset: Finish, Clearly Unfinish, Near-finished Unfinish.
3. Create ROI metadata CSV with bounding boxes or fixed crop coordinates.
4. Generate fixed ROI crops.
5. Generate bbox ROI crops.
6. Build `full_sft_v1.json`.
7. Build `roi_only_sft_v1.json`.
8. Build `full_roi_mixed_sft_v1.json`.
9. Build full-image and ROI evaluation JSON files.
10. Verify that every image path in JSON exists under `python/data`.
11. Run a small dry-run inference on 5-10 samples before training.
12. Record training configuration and output directory name.

## Preparation Script

### Interactive Bounding-Box Annotation

Use the interactive annotation tool instead of manually entering coordinates:

```text
python/src/annotate_roi_boxes.py
```

Example command:

```bash
python python/src/annotate_roi_boxes.py ^
  --input-root python/data/roi_annotation_input ^
  --output-csv python/data/roi_annotations_v1.csv ^
  --data-root python/data ^
  --part "Port End Cover" ^
  --preview-root python/data/roi_annotation_previews
```

For each image, drag a bounding box around the target part and include enough surrounding
context to judge its relationship with the mating component. Confirm the selection with
Enter or Space. The annotation is saved immediately, so the tool can be closed and resumed
without losing completed work.

The optional preview directory stores a copy with the selected bounding box drawn on it,
which should be reviewed before generating the final crops.

A helper script is provided at:

```text
python/src/prepare_roi_mixed_dataset.py
```

Metadata template:

```text
python/data/roi_annotations_template.csv
```

Example command:

```bash
python python/src/prepare_roi_mixed_dataset.py ^
  --metadata python/data/roi_annotations_template.csv ^
  --output-root python/data/roi_experiment ^
  --margin 0.15
```

## Paper-Ready Experiment Section: ROI-Aligned Verification

### ROI-Aligned Dataset Construction

To examine whether local visual supervision improves completion verification, we constructed an ROI-aligned dataset for the `Port End Cover` assembly stage. The dataset was collected from three previously recorded verification frame sets and filtered to retain only cover-related samples. Each image was assigned a binary completion label, `Finish` or `Unfinish`, according to the filename-derived ground-truth status and was then manually annotated with a bounding box around the target cover region. The bounding box was drawn to include both the cover and its immediate mating context, since assembly completion depends not only on the part itself but also on local relational cues such as edge alignment, hole registration, seating, and visible gaps.

The final ROI annotation file contains 715 labeled images, including 320 `Finish` samples and 395 `Unfinish` samples. For each image, the metadata record includes the original image path, the target part name, the completion label, and the bounding-box coordinates. ROI crops were generated by expanding each annotated bounding box by 15% along both spatial dimensions before cropping. This margin was used to preserve local contextual information around the part while suppressing irrelevant background regions.

The resulting dataset was split at the source-image level into training, validation, and test subsets using a fixed random seed. The split contained 500 training images, 107 validation images, and 108 test images. The same source split was used for all full-image and ROI-based variants to ensure that performance differences are attributable to input representation and training distribution rather than different data partitions.

### Training Dataset Variants

Three single-image supervised fine-tuning datasets were generated from the same source-image split:

```text
Full-only training:
  python/data/roi_experiment_v1/sft/full_sft_v1.json
  500 training samples

ROI-only training:
  python/data/roi_experiment_v1/sft/roi_only_sft_v1.json
  500 training samples

Full+ROI mixed training:
  python/data/roi_experiment_v1/sft/full_roi_mixed_sft_v1.json
  1000 training samples
```

In the full-only setting, each sample contains the original full-frame image and asks the model to determine whether the `Port End Cover` assembly state is `Finish` or `Unfinish`. In the ROI-only setting, the original image is replaced by the corresponding bounding-box crop. In the Full+ROI mixed setting, each source training image contributes two independent single-image samples: one full-frame sample and one ROI-crop sample. This design keeps the training format compatible with the original VLM pipeline while exposing the model to both global assembly context and enlarged local completion cues.

All variants use the same structured target format:

```json
{"part": "Port End Cover", "verification": "Finish/Unfinish"}
```

This constrained output format enables direct metric computation and reduces ambiguity in parsing model predictions.

### Training Regime

For the final paper experiments, all three dataset variants should be trained with full supervised fine-tuning from the same `Qwen2.5-VL-7B-Instruct` base model. Earlier low-bit LoRA fine-tuning runs were useful for rapid prototyping and pipeline validation, but they should not define the main published comparison once full-SFT training on `8 x H200` GPUs is available. Using a common full-SFT regime improves fairness across variants and avoids conflating ROI effects with parameter-efficient adaptation choices.

### Evaluation Protocol

Validation and test files were generated for both full-frame and ROI-crop inputs:

```text
Validation:
  python/data/roi_experiment_v1/eval/val_full_v1.json
  python/data/roi_experiment_v1/eval/val_roi_v1.json

Test:
  python/data/roi_experiment_v1/eval/test_full_v1.json
  python/data/roi_experiment_v1/eval/test_roi_v1.json
```

The evaluation is designed to separate two effects. First, comparing full-frame and ROI-crop inference evaluates whether local visual focus improves completion judgment at test time. Second, comparing models trained on full-only, ROI-only, and Full+ROI mixed data evaluates whether ROI-aligned fine-tuning improves the model's learned sensitivity to local assembly features rather than merely changing the prompt-induced response tendency.

The recommended evaluation matrix is:

```text
Model trained on full-only data      -> evaluated on full-frame test images
Model trained on full-only data      -> evaluated on ROI-crop test images
Model trained on ROI-only data       -> evaluated on ROI-crop test images
Model trained on Full+ROI mixed data -> evaluated on full-frame test images
Model trained on Full+ROI mixed data -> evaluated on ROI-crop test images
```

The main comparison should emphasize the Full+ROI mixed model because it tests whether local feature supervision can be incorporated without discarding the global context available in the original full-frame images.

### Metrics

Completion verification is treated as a binary classification problem. Unless otherwise stated, `Finish` is treated as the positive class. The following metrics should be reported:

```text
Accuracy
Precision
Recall
F1-score
False positive rate
False negative rate
Completion judgment accuracy
```

In this task, false positives are especially important because they correspond to incomplete assemblies being incorrectly accepted as completed. Therefore, the analysis should explicitly report the false acceptance behavior for `Unfinish` samples, particularly for visually near-complete cases when such hard-case annotations are available.

### Expected Result Interpretation

If ROI-crop evaluation improves performance for the full-only model, the result suggests that the original full-frame input contains distracting background information or insufficient visual scale for the target completion cues. However, this alone would not prove that the model has learned stronger local feature perception.

If ROI-only or Full+ROI mixed fine-tuning improves F1-score and reduces false positives on `Unfinish` samples, the result provides stronger evidence that ROI-aligned supervision improves the VLM's ability to perceive task-relevant assembly features. In particular, an improvement of the Full+ROI mixed model on both full-frame and ROI-crop test inputs would support the claim that the model benefits from local feature supervision while retaining robustness to the original deployment view.

### Implementation Details

The ROI dataset was generated with:

```bash
python python/src/prepare_roi_mixed_dataset.py ^
  --metadata python/data/roi_annotations_v1.csv ^
  --output-root python/data/roi_experiment_v1 ^
  --margin 0.15 ^
  --seed 42 ^
  --train-ratio 0.70 ^
  --val-ratio 0.15
```

This command produced 715 ROI crops under:

```text
python/data/roi_experiment_v1/images_roi_bbox/
```

and the corresponding split metadata under:

```text
python/data/roi_experiment_v1/metadata/
```

The script performs the following preparation steps:

```text
Validate metadata image paths and bounding boxes
Generate bbox ROI crops
Create stratified train/val/test split CSV files
Create full-only SFT JSON
Create ROI-only SFT JSON
Create Full+ROI mixed SFT JSON
Create full-image and ROI evaluation JSON files
```

Generated files:

```text
python/data/roi_experiment_v1/images_roi_bbox/
python/data/roi_experiment_v1/metadata/split_train_v1.csv
python/data/roi_experiment_v1/metadata/split_val_v1.csv
python/data/roi_experiment_v1/metadata/split_test_v1.csv
python/data/roi_experiment_v1/sft/full_sft_v1.json
python/data/roi_experiment_v1/sft/roi_only_sft_v1.json
python/data/roi_experiment_v1/sft/full_roi_mixed_sft_v1.json
python/data/roi_experiment_v1/eval/val_full_v1.json
python/data/roi_experiment_v1/eval/val_roi_v1.json
python/data/roi_experiment_v1/eval/test_full_v1.json
python/data/roi_experiment_v1/eval/test_roi_v1.json
```

## Notes for Implementation

The current training pipeline should be kept single-image at first. Multi-image input such as Full Image + ROI should only be introduced after the single-image ROI experiments are complete, because multi-image inference introduces an additional distribution shift unless the model is trained with the same format.

The first publishable ROI experiment should therefore focus on:

```text
Full-only vs ROI-only vs Full+ROI mixed
```

not on multi-image inference.

## New Machine Setup

If the project is resumed on another computer using only the GitHub repository, the following assets should be available directly after cloning:

```text
python/data/2.3vlm_status_frames/
python/data/3.14vlm_verification_frames/
python/data/3.16test_vlm_verification_frames/
python/data/roi_annotation_input/
python/data/roi_experiment_v1/
python/data/*.json
python/output/v1_lora_baseline/
python/output/v3.14_few_shot_verification/
python/output/v3.15_few_shot_verification/
```

These uploaded assets cover:

```text
Original frame data for earlier verification experiments
ROI annotation source images
ROI-aligned crops, split metadata, and SFT/eval JSON files
Selected previously trained LoRA adapters for comparison or warm-start reference
```

### Base Model to Download

The base VLM is not stored in this repository. On a new machine, download:

```text
Qwen/Qwen2.5-VL-7B-Instruct
```

Recommended local location:

```text
python/models/Qwen2.5-VL-7B-Instruct
```

The training script now defaults to this repository-local model path. It can also be overridden with:

```bash
set VLM_MODEL_ID=python/models/Qwen2.5-VL-7B-Instruct
```

### Hardware Assumption for Main Paper Runs

The current intended hardware for the main paper experiments is:

```text
8 x H200 GPUs
```

Under this hardware assumption:

```text
Main experiments should use full SFT.
Do not treat 4-bit loading as the main default.
Do not treat LoRA as the main paper training strategy.
```

LoRA-based runs can still be preserved in the repository for:

```text
historical comparison
engineering baselines
quick pilot checks
```

### Training Script Defaults

The training entry point `python/src/train_lora.py` now defaults to:

```text
Model:
  python/models/Qwen2.5-VL-7B-Instruct

Training data:
  python/data/roi_experiment_v1/sft/full_roi_mixed_sft_v1.json

Experiment name:
  roi_mixed_full_roi_finetune_v1
```

Note that `train_lora.py` is now best interpreted as a legacy or transitional training entry point. The main paper direction has shifted to full SFT from the base model rather than LoRA-based adaptation.

You can switch experiments without editing the script by setting:

```bash
set VLM_MODEL_ID=...
set VLM_DATA_FILE=...
set VLM_EXPERIMENT_NAME=...
```
