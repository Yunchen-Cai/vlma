# Codex Handoff

## Purpose

This document is a detailed handoff for the next Codex instance. It summarizes:

- what this repository contains
- what work has been completed in this conversation
- what has already been pushed to GitHub
- what still remains local only
- what the paper is trying to claim
- what the next experiments should be

The user is continuing an academic project on assembly verification with VLMs and wants the repository to be self-sufficient for work on another computer that can only download from GitHub.

## Repository Overview

This repository contains three major parts:

### 1. Python VLM pipeline

Main purpose:

- data preparation
- VLM fine-tuning
- evaluation
- ROI-based experiment setup

Important locations:

- `python/src/`
- `python/data/`
- `python/output/`
- `python/ROI_MIXED_EXPERIMENT.md`

### 2. Java backend

Directory:

- `VideoAssemblyMonitor/`

Purpose:

- assembly monitoring backend
- process/state-machine services
- image sending / application logic

There are unrelated local Java changes in the worktree that were intentionally not committed during this ROI/Git task.

### 3. Frontend

Directory:

- `VideoAssemblyMonitorWeb/`

Purpose:

- web UI for monitoring / visualization

This part was not modified in the recent ROI experiment work.

## Research Goal

The user is preparing a high-level academic paper around:

- manual assembly scene understanding
- completion verification
- VLM-based feature perception
- ROI-aligned supervision
- eventual process-constrained verification with SOP/FSM

The core scientific concern is:

> Has the VLM really learned key visual completion cues, or is it only showing prompt bias?

The ROI experiment was designed to provide stronger evidence for feature learning rather than prompt-only behavior change.

## Paper Direction

The paper direction developed in this conversation is:

- use ROI-based supervision to improve local feature sensitivity
- compare full-image training, ROI-only training, and Full+ROI mixed training
- show stronger completion verification on subtle hard negatives
- later combine with SOP/FSM constraints for process-level robustness

Target experiment families discussed:

- `Full-only`
- `ROI-only`
- `Full+ROI mixed`
- `VLM only`
- `VLM + SOP prompt`
- `VLM + SOP + FSM`

Required evaluation dimensions discussed:

- accuracy
- precision
- recall
- F1
- false positive rate
- false negative rate
- completion judgment accuracy
- hard-case analysis
- data efficiency curve

## ROI Experiment Work Completed

### ROI data collection and annotation

The user chose `Port End Cover` as the pilot part.

We created:

- `python/src/collect_cover_roi_input.py`
- `python/src/annotate_roi_boxes.py`
- `python/src/prepare_roi_mixed_dataset.py`
- `python/data/roi_annotations_template.csv`

Workflow completed:

1. cover images were collected from:
   - `python/data/2.3vlm_status_frames`
   - `python/data/3.14vlm_verification_frames`
   - `python/data/3.16test_vlm_verification_frames`
2. images were copied into:
   - `python/data/roi_annotation_input/Finish`
   - `python/data/roi_annotation_input/Unfinish`
3. user manually annotated bounding boxes
4. final annotation CSV was created:
   - `python/data/roi_annotations_v1.csv`

Final annotation size:

- 715 labeled images total
- 320 `Finish`
- 395 `Unfinish`

### ROI dataset generation

The generated experiment directory is:

- `python/data/roi_experiment_v1/`

Generated assets:

- ROI crops
- train/val/test split CSVs
- SFT JSON files
- eval JSON files

Key generated files:

- `python/data/roi_experiment_v1/sft/full_sft_v1.json`
- `python/data/roi_experiment_v1/sft/roi_only_sft_v1.json`
- `python/data/roi_experiment_v1/sft/full_roi_mixed_sft_v1.json`
- `python/data/roi_experiment_v1/eval/val_full_v1.json`
- `python/data/roi_experiment_v1/eval/val_roi_v1.json`
- `python/data/roi_experiment_v1/eval/test_full_v1.json`
- `python/data/roi_experiment_v1/eval/test_roi_v1.json`

Split size:

- train: 500 source images
- val: 107 source images
- test: 108 source images

Training sample count:

- full-only: 500
- ROI-only: 500
- Full+ROI mixed: 1000

### ROI documentation

The main experiment planning and paper-ready experiment wording are recorded in:

- `python/ROI_MIXED_EXPERIMENT.md`

This file already contains:

- experiment rationale
- dataset construction
- directory structure
- training variants
- evaluation protocol
- expected interpretation
- new-machine setup notes

## Training Script Changes

File:

- `python/src/train_lora.py`

Important recent changes:

- removed dependence on the old absolute Windows path for the model
- now defaults to a repo-local model directory:
  - `python/models/Qwen2.5-VL-7B-Instruct`
- now defaults to ROI mixed training data:
  - `python/data/roi_experiment_v1/sft/full_roi_mixed_sft_v1.json`
- now supports environment-variable overrides:
  - `VLM_MODEL_ID`
  - `VLM_DATA_FILE`
  - `VLM_EXPERIMENT_NAME`

Note:

- the base Qwen model itself is not in this repository
- it must be downloaded separately on the new machine

## Base Model Required on New Machine

The new machine should download:

- `Qwen/Qwen2.5-VL-7B-Instruct`

Recommended local location:

- `python/models/Qwen2.5-VL-7B-Instruct`

If needed, the script can also use:

- `VLM_MODEL_ID=<path-or-model-id>`

## Git and Upload Work Completed

### Already pushed to GitHub

Remote repository:

- `https://github.com/Yunchen-Cai/vlma.git`

Branch:

- `main`

Previously pushed ROI-related commit:

- `87047f2`
  - added ROI scripts
  - added ROI experiment documentation
  - added `roi_annotation_input`
  - added `roi_experiment_v1`
  - added ROI CSV metadata
  - added `.gitattributes`
  - updated `.gitignore`

During this conversation, another push succeeded:

- `da6ff44`
  - added portable training config and dataset manifests
  - added `python/data/*.json`
  - updated `python/src/train_lora.py`
  - updated `python/ROI_MIXED_EXPERIMENT.md`

### Git LFS setup

File created:

- `.gitattributes`

Tracked via LFS:

- `*.pth`
- `*.bin`
- `*.dat`
- `*.safetensors`
- `*.ckpt`
- `*.onnx`

This was added so LoRA adapters and future checkpoints can be uploaded safely.

## Local-Only Resources Still Not Pushed

These still exist only in the local working tree and have not yet been pushed:

### Raw frame directories

- `python/data/2.3vlm_status_frames/`
- `python/data/3.14vlm_verification_frames/`
- `python/data/3.16test_vlm_verification_frames/`

Measured sizes:

- `2.3vlm_status_frames`: 261,295,891 bytes
- `3.14vlm_verification_frames`: 268,485,717 bytes
- `3.16test_vlm_verification_frames`: 346,281,037 bytes

### LoRA adapters intended for upload

These are the selected final adapters that should eventually be pushed:

- `python/output/v1_lora_baseline/`
- `python/output/v3.14_few_shot_verification/`
- `python/output/v3.15_few_shot_verification/`

Only the final adapter files were intended for upload, not redundant intermediate checkpoint folders.

### Why they were not pushed yet

The work was reorganized into smaller pushes because large pushes repeatedly failed due to unstable GitHub HTTPS connectivity.

Observed failures included:

- `Recv failure: Connection was reset`
- `Could not connect to github.com port 443`

At the moment of writing this handoff:

- the JSON/config push has succeeded
- the three large raw-frame directories are still untracked local directories
- the LoRA adapters still remain local only

## Current Local Worktree Status

As of the latest check, unrelated local changes still exist and were intentionally left untouched:

- `.idea/gradle.xml`
- `.idea/misc.xml`
- `.idea/modules/demo.main.iml`
- `.idea/vlma.iml`
- `VideoAssemblyMonitor/build.gradle`
- `VideoAssemblyMonitor/src/main/java/nusri/fyp/demo/service/StateMachineService.java`
- `VideoAssemblyMonitor/src/main/java/nusri/fyp/demo/service/VideoService.java`
- `VideoAssemblyMonitor/src/main/java/nusri/fyp/demo/service/img_sender/ImageSenderService.java`
- `VideoAssemblyMonitor/src/main/java/nusri/fyp/demo/state_machine/StateMachine.java`
- `python/.idea/vcs.xml`
- `python/src/qwen_server_verification.py`
- `.ai/`
- `.idea/dataSources.xml`
- `.vs/`
- `.vscode/`
- `VideoAssemblyMonitor/src/test/`

These are not part of the ROI upload work and were deliberately not committed.

## Important Files Created or Updated in This Conversation

Created:

- `CODEX_HANDOFF.md`
- `.gitattributes`
- `python/ROI_MIXED_EXPERIMENT.md`
- `python/src/annotate_roi_boxes.py`
- `python/src/collect_cover_roi_input.py`
- `python/src/prepare_roi_mixed_dataset.py`
- `python/data/roi_annotations_template.csv`

Updated:

- `.gitignore`
- `python/src/train_lora.py`

Generated and pushed:

- `python/data/roi_annotations_v1.csv`
- `python/data/roi_annotation_input/...`
- `python/data/roi_experiment_v1/...`
- `python/data/*.json`

## Experiment Logic and Planned Results

The intended main ROI comparison is:

1. `Full-only`
2. `ROI-only`
3. `Full+ROI mixed`

Recommended evaluation matrix:

1. train full-only -> test full
2. train full-only -> test ROI
3. train ROI-only -> test ROI
4. train Full+ROI mixed -> test full
5. train Full+ROI mixed -> test ROI

The scientific interpretation should focus on:

- whether ROI inference alone helps
- whether ROI-aligned training actually improves local feature perception
- whether performance gains reduce false acceptance on `Unfinish`

## Full Experiment Plan Going Forward

The agreed broad plan is:

### Stage 1. Main ROI result

- run `Full-only`
- run `ROI-only`
- run `Full+ROI mixed`

### Stage 2. Verification metrics

For each model, report:

- accuracy
- precision
- recall
- F1
- false positive rate
- false negative rate
- completion judgment accuracy

### Stage 3. Hard cases

Recommended hard cases:

- near-finished unfinish
- occlusion
- illumination variation
- wrong tool
- wrong order

### Stage 4. Data efficiency

Use training fraction as x-axis, e.g.:

- 10%
- 20%
- 40%
- 60%
- 80%
- 100%

Compare at least:

- `Full-only`
- `Full+ROI mixed`

### Stage 5. Ablation on process guidance

Recommended:

- `VLM only`
- `VLM + SOP prompt`
- `VLM + SOP + FSM`

### Stage 6. Qualitative analysis

Add:

- success/failure case visualization
- confusion matrix
- near-finished false acceptance examples

## Immediate Next Steps for the Next Codex

The most useful next actions are:

1. push the three large raw-frame directories in smaller batches
2. push the selected final LoRA adapters through Git LFS
3. add a clean evaluation script that can consume model outputs and produce:
   - accuracy
   - precision
   - recall
   - F1
   - FPR
   - FNR
   - completion judgment accuracy
4. optionally create a dedicated training launcher for:
   - `full_sft_v1.json`
   - `roi_only_sft_v1.json`
   - `full_roi_mixed_sft_v1.json`

## Suggested Push Order for Remaining Assets

When network is stable, push in this order:

1. `python/data/2.3vlm_status_frames/`
2. `python/data/3.14vlm_verification_frames/`
3. `python/data/3.16test_vlm_verification_frames/`
4. `python/output/v1_lora_baseline/adapter_*`
5. `python/output/v3.14_few_shot_verification/adapter_*`
6. `python/output/v3.15_few_shot_verification/adapter_*`

Avoid pushing all remaining large assets in one single commit if the network remains unstable.

## Key User Preference Notes

- The user wants GitHub to contain not only scripts but also the datasets and model-related assets needed on the new machine.
- The new machine can only obtain materials from GitHub, so reproducibility through repository contents matters a lot.
- The user is writing a high-level academic paper and wants experiment records in a paper-ready style.
- The user values practical execution over theoretical discussion and often wants the agent to directly run or prepare the actual workflow.
