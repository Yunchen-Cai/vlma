# Paper Writing Handoff — VLMA Manuscript

**Purpose.** This document is for the next agent (or human collaborator) who picks up the **paper-writing** workstream on the VLMA project. It is the single place to look for: what the paper claims, where each claim lives in the manuscript, what evidence backs it, what state the artifacts are in, and what the open todo list is.

It is intentionally separate from `CODEX_HANDOFF.md` (which describes the experimental pipeline + cloud commands) and from `python/ROI_MIXED_EXPERIMENT.md` (which describes the experiment protocol). Read this one **first** if your job is to finish the manuscript; the other two are reference material you will reach for as you write.

Last sync: 2026-06-17. Treat any date older than 2 weeks as stale and re-verify from the source files listed below.

---

## 1. Project elevator pitch

**Title.** ROI-Aligned Vision-Language Verification and SOP-Guided State Machine for Manual Assembly Monitoring.

**Authors.** Yunchen Cai, Binghong Liu, Soh Khim Ong*, Andrew Y. C. Nee*. NUS Mechanical Engineering, College of Design and Engineering.

**One-sentence claim.** A single Qwen2.5-VL-7B model, fine-tuned with ROI-aligned supervision and operated in two prompt-switched inference modes (General + Verification), combined with an SOP-guided probabilistic state machine and a zero-shot open-vocabulary ROI provider (Grounding DINO Tiny), produces an in-line manual-assembly monitoring system that closes the perception–procedure–deployment loop and verifies completion of every SOP step rather than merely recognising actions.

**Where the novelty lives.** Three places, in order of importance:
1. **ROI-aligned supervision** — each annotated source frame contributes both a full-frame and an ROI-cropped training sample to one shared VLM. Cuts FPR on Unfinish samples from 14.93 % to 0.69 % on a strictly held-out single-part test, and from 60.23 % to 0.00 % on a four-part benchmark.
2. **SOP-guided probabilistic FSM that consumes language-typed observations from the VLM** — observations are action–object strings drawn from the SOP white-list, weighted by the VLM's token-level confidence. Distinct from prior "detector + FSM" stacks.
3. **Open-vocabulary ROI provider closes the deployment loop** — Grounding DINO Tiny takes the SOP-active part name as a text prompt; system end-to-end without a fixed-class detector.

**One-sentence target venue framing.** RCIM-style journal paper (we have already restructured to match Q. Ye et al. 2026 RCIM as the sample paper). Currently formatted for MDPI *Sensors* / *Machines* depending on supervisor's call (see §11 below).

---

## 2. Manuscript file inventory

All paths are absolute. **The English docx is canonical**; the Chinese docx and English markdown derive from it.

| File | Role | When to touch |
|---|---|---|
| `/Users/caiyunchen.3/vlma_paper_draft_v1_en.docx` | **Canonical English manuscript** | Every edit starts here |
| `/Users/caiyunchen.3/vlma_paper_draft_v1_zh.docx` | Chinese mirror, regenerated from English | After substantive English edits |
| `/Users/caiyunchen.3/vlma_paper_draft_v1.md` | English markdown export | After substantive English edits |
| `/Users/caiyunchen.3/vlma_paper_draft_v1_en_BACKUP_before_*.docx` | Snapshots before risky rounds | Read-only; revert from here if a round breaks the docx |
| `/Users/caiyunchen.3/vlma/CODEX_HANDOFF.md` | Experiment pipeline + cloud commands (English) | Reference, not edit, when planning new experiments |
| `/Users/caiyunchen.3/vlma/CODEX_HANDOFF_ZH.md` | Same, Chinese mirror | Same |
| `/Users/caiyunchen.3/vlma/python/ROI_MIXED_EXPERIMENT.md` | Detailed experiment protocol | Reference when verifying any §4 number |
| `/Users/caiyunchen.3/vlma/python/ROI_MIXED_EXPERIMENT_ZH.md` | Same, Chinese mirror | Same |

### docx editing rules

1. Always back up before any non-trivial edit: `cp .../vlma_paper_draft_v1_en.docx .../vlma_paper_draft_v1_en_BACKUP_before_<your-tag>.docx`.
2. Edit via `python-docx`. Never hand-edit the .docx XML.
3. Preserve first-run formatting (font name, font size). The east-asian font slot must be `Times New Roman` (English) or `SimSun` (Chinese mirror) — set explicitly via `w:rFonts`.
4. Heading style names in this document are `Heading 1`, `Heading 2`, `Heading 3` (with the space). The Heading 1 style's internal `pStyle val` is `1`, not `Heading1` — match on both spellings when filtering.
5. Captions are plain `Normal` paragraphs that start with `Fig. N — Title.` or `Table N — Title.` (em-dash, single-sentence form, ending in a period). Never `Figure N.` (Elsevier style).
6. Equations are numbered with a tab-aligned `(N)` at the right end of the line.
7. Cross-references use `_Sec_N_M`, `_Fig_N`, `_Tab_N`, `_Eq_N`, `_App_X`, `_Ref_N` bookmarks plus matching `w:hyperlink w:anchor=...`. Any unresolved anchor is a defect.

A reusable helper `replace_paragraph_text(p, new_text)` is in `/tmp/refnum.py` and `/tmp/restructure_36.py`; copy it into any new edit script.

---

## 3. Current manuscript structure and word counts (verified 2026-06-17)

```
Abstract                                                  446 words
1. Introduction                                         1 194 words   (8 paragraphs)
2. Related Work                                         1 064 words   (11 paragraphs)
   2.1 Action Recognition and Process Monitoring in Manual Assembly
   2.2 Vision-Language and Multimodal Models in Industrial Scenarios
   2.3 Neuro-Symbolic Process Monitoring
3. Methodology                                          4 562 words   (59 paragraphs)
   3.1 System Overview
   3.2 Data acquisition setup
   3.3 ROI-aligned supervision
   3.4 Dual-mode VLM adaptation
   3.5 SOP-guided state machine and deployment architecture
   3.6 ROI provider                  ← added 2026-06-17 for Grounding DINO Tiny
4. Experiments                                          4 566 words   (57 paragraphs)
   4.1 Experimental Setup
   4.2 ROI-aligned supervision for completion verification
       4.2.1 Experimental setup
       4.2.2 Results and comparative analysis
   4.3 Unified multi-task integration and deployment robustness
       4.3.1 Experimental setup
       4.3.2 Results and comparative analysis (contains: unified MT, ROI perturbation, Grounding DINO end-to-end)
   4.4 Comparison with a fixed-class CNN baseline
       4.4.1 Experimental setup
       4.4.2 Results and comparative analysis
5. Conclusion and Future Work                           2 140 words   (24 paragraphs)
   5.1 Discussion
   5.2 Limitations
   5.3 Conclusion
References                                                  671 words   (21 entries)
Appendix A. Prompt Texts
   A.1 General-Mode Prompt
   A.2 Verification-Mode Prompt
   A.3 Guided Long Prompt (used in Section 4.2.2 ablation)
Appendix B. Training hyperparameters
Appendix C. Per-part breakdown of the cross-part zero-shot evaluation
                                                       TOTAL ~15 200 words
```

11 tables and 11 figures. Equation count (1)–(4) in §3.1.

---

## 4. Headline numbers — the table you need to memorise

These are the numbers that show up across the abstract, §4, §5.1, and the discussion. When you cite a number in the manuscript, it MUST match this table; if you see a divergence, the manuscript is wrong, not this table.

### 4.1 Single-part (Port End Cover), held-out 3.16 test (n = 285 frames)

| Variant | Accuracy | Precision | Recall | F1 | FPR |
|---|---:|---:|---:|---:|---:|
| Full-only | 92.11 % | 0.8669 | 0.9929 | 0.9256 | **14.93 %** (21 / 144) |
| ROI-only | 97.89 % | 0.9891 | 0.9681 | 0.9785 | 1.04 % (1 / 144) |
| **Full + ROI mixed** | **99.30 %** | 0.9929 | 0.9929 | 0.9929 | **0.69 %** (1 / 144) |

### 4.2 Four-part held-out test (n = 224 view-level)

| Variant | Accuracy | F1 | FPR | Unfinish Acc. |
|---|---:|---:|---:|---:|
| Full-only | 60.65 % | 0.7837 | 60.23 % | 29.17 % |
| ROI-only | 97.77 % | 0.9749 | 0.00 % | 100.00 % |
| **Full + ROI mixed** | **100.00 %** | 1.0000 | **0.00 %** | 100.00 % |

Wilson 95 % upper bound on the four-part Full + ROI mixed zero-error result: **1.67 %** (on 224 combined-view), 3.05 % (on 122 Unfinish), 3.63 % (on 102 Finish).

### 4.3 Guided-prompt ablation, single-part held-out (n = 570 view-level)

| Prompt variant | Accuracy | Finish Acc. | Unfinish Acc. | FPR |
|---|---:|---:|---:|---:|
| Plain (recommended) | 99.30 % | 99.29 % | 99.31 % | 0.69 % |
| Guided short | n/a* (JSON broken) | n/a* | n/a* | n/a* |
| Guided long | 66.44 % | 87.92 % | 46.93 % | **52.97 %** |

### 4.4 Unified multi-task, no-phase, multi-part test

| Variant | Joint ATP | Verification Acc. | Verification FPR | Unfinish Acc. |
|---|---:|---:|---:|---:|
| General ATP-only | 89.54 % | 49.11 % | 11.48 % | 88.52 % |
| ATP + V (Full-only) | 83.30 % | 88.84 % | 7.38 % | 92.62 % |
| **ATP + V (Full + ROI mixed)** | **91.56 %** | **99.11 %** | **0.00 %** | 100.00 % |

### 4.5 ROI perturbation sensitivity (Full + ROI mixed on 4-part test)

| Setting | Accuracy | FPR | Unfinish Acc. |
|---|---:|---:|---:|
| GT ROI | 100.00 % | 0.00 % | 100.00 % |
| Centre offset ± 5 % | 100.00 % | 0.00 % | 100.00 % |
| Centre offset ± 10 % | 95.54 % | 8.20 % | 91.80 % |
| Centre offset ± 15 % | 97.32 % | 3.28 % | 96.72 % |
| Scale jitter ± 10 % | 97.32 % | 4.92 % | 95.08 % |
| Scale jitter ± 20 % | 96.43 % | 6.56 % | 93.44 % |
| Full-only (reference) | 60.65 % | 60.23 % | 29.17 % |

### 4.6 Grounding DINO Tiny end-to-end (Table 8)

⚠️ **NUMBERS PENDING**. The Grounding DINO cloud run was launched 2026-06-17 (cf. §9 below). Once results are in, fill the placeholders `@@IOU_MEAN@@`, `@@IOU_MEDIAN@@`, `@@IOU_MIN@@`, `@@DET_RATE@@`, `@@DET_ACC@@`, `@@DET_FPR@@` in:
- §4.3.2 results paragraph (search the docx for `The ROI provider of Section 3.6 is now evaluated end-to-end`)
- Table 8 cells (third row: "Grounding DINO Tiny (zero-shot)")
- Abstract / §5 if you decide to highlight in those locations

### 4.7 YOLOv8n-cls few-shot baseline (Table 9)

| N | Accuracy | FPR | Unfinish Acc. |
|---|---:|---:|---:|
| 50 | 99.07 ± 1.31 % | 1.59 ± 2.24 % | 98.41 ± 2.24 % |
| 100 | 100.00 ± 0.00 % | 0.00 ± 0.00 % | 100.00 ± 0.00 % |
| 200–400 | 100.00 ± 0.00 % | 0.00 ± 0.00 % | 100.00 ± 0.00 % |

Three seeds. **This table is the only place in the paper that uses multi-seed reporting** — every other VLM result is single-seed.

### 4.8 Cross-part zero-shot, Cover-only Full+ROI mixed on 4-part test (Appendix C)

| Part | GT-F → Pred-F | GT-F → Pred-U | GT-U → Pred-U | GT-U → Pred-F |
|---|---:|---:|---:|---:|
| Port End Cover (in-dist) | 13 | 0 | 18 | 0 |
| Drive Gear (unseen) | 0 | 13 | 16 | 0 |
| Gear Housing (unseen) | 0 | 15 | 14 | 0 |
| Thrust Block (unseen) | 0 | 10 | 13 | 0 |
| **Aggregate** | **13 / 51** | **38 / 51** | **61 / 61** | **0 / 61** |

Apparent aggregate FPR 0 % is a **degenerate "Unfinish-by-default"** — explicitly disclaim this in §5.2.

---

## 5. Paper narrative — what claim sits where

This is the load-bearing map. If you change the narrative, change every cell.

| Claim | Stated in | Defended in | Numbers |
|---|---|---|---|
| Manual assembly verification ≠ action recognition | §1 ¶2; §2.1 last; §5.1 first | §4.2.2 single-part Full-only failure; §4.3.2 ATP-only failure (49.11 % acc) | 14.93 % → 0.69 % single-part; 49.11 % ATP-only verification acc |
| ROI-aligned supervision is the load-bearing component | §3.3; §5.1 §1 | §4.2.2 + §4.3.2 + §4.4 sensitivity (multiple sources) | 14.93→0.69 (1-part); 60.23→0.00 (4-part); 99.11 % unified |
| Prompt engineering does not substitute for ROI supervision | §3.4; §5.1 §2 | §4.2.2 guided-prompt ablation | Guided long → 46.93 % Unfinish acc, 52.97 % FPR |
| Single VLM serves both modes with one set of weights | §3.4; §5.1 §3 | §4.3.2 unified table | 91.56 % joint ATP + 99.11 % verification simultaneously |
| ROI-supervision gain survives detector perturbation | §3.5 sensitivity para; §5.1 §5 | §4.3.2 perturbation table | Worst FPR 8.20 % vs Full-only 60.23 % across full ±5–±15 % / ±10–±20 % envelope |
| Open-vocabulary ROI provider closes the loop end-to-end | §3.6; §5.1 §5 (extend) | §4.3.2 Grounding DINO row of Table 8 | **PENDING** — fill once cloud run completes |
| Small CNN matches narrow benchmark but cannot replace VLM at system level | §4.4; §5.1 §6 | §4.4 Table 9 + §4.4.2 three differences | YOLO @ N=100: 100 % / 0 % FPR; same ceiling as VLM on cropped binary task |
| Verification does NOT transfer zero-shot to unseen parts | §5.2 last; Appendix C | §4.3.2 not directly; Appendix C confusion table | Cover-only on 4-part: 0 / 38 unseen Finish recovered |

---

## 6. Reference numbering — the rule and the current map

Order is **strictly first-appearance in body**, RCIM/Elsevier convention. Last renumber: 2026-06-15. The current map is:

```
[1]  Navyasri & Suma 2025         — key-frame extraction
[2]  Chen et al. 2020             — repetitive assembly action recognition
[3]  Ay & Emel 2024               — YOLOv8 + LSTM assembly validation
[4]  Cicirelli et al. 2022        — HA4M assembly benchmark
[5]  Riedel et al. 2022           — MTM-1 hand-gesture graph CNN
[6]  Kang et al. 2024             — spatial-temporal-contact features
[7]  Al-Amin et al. 2022          — multimodal IMU+EMG+Kinect fusion
[8]  Hui et al. 2024              — Qwen2.5 technical report
[9]  Huang et al. 2025            — LEGO Co-builder (fine-grained VLM benchmark)
[10] Xu et al. 2025               — Anomaly-OV (look-twice for industrial VLM)
[11] Oyekan et al. 2020           — RGB-D + HMM assembly tracking
[12] Selvaraj et al. 2024         — SMIRL (augmented inference state machine)
[13] Zhang et al. 2026            — Learning-based stage verification (YOLO+LSTM+FSM)
[14] Torres et al. 2021           — SHERPA / HEART human-error analysis
[15] Liu et al. 2025              — VLM-enhanced embodied agents for HRC
[16] Murata 1989                  — Petri nets (canonical reference)
[17] van der Aalst 2016           — Process Mining textbook
[18] Wei et al. 2022              — Finetuned LMs are zero-shot learners
[19] Caterpillar Inc. 2024        — gear pump part no. 333-3781
[20] Hu et al. 2019               — See better before looking closer (WSDAN)
[21] Sclar et al. 2024            — prompt-sensitivity quantification
[22] Liu et al. 2024              — Grounding DINO (ECCV)            ← added 2026-06-17
```

If you add a new reference, append at the **end** (next free number); only re-run the full first-appearance reorder if you do a major restructure.

---

## 7. Open writing tasks — prioritised

### P0 (must finish before submission)

1. **Fill the Grounding DINO numbers** once the cloud experiment lands. Six placeholders in §4.3.2 + Table 8. Source of truth: `/mnt/workspace/users/caiyunchen/vlma/python/data/roi_experiment_v2_4part/eval_grounding_dino/iou_summary.json` and `python/output/eval/grounding_dino_roi_provider_eval/metrics_summary.csv`. Helper: write a 30-line Python that opens the docx, regex-replaces the six `@@*@@` tokens. Then also fill Table 8 row 3.
2. **Re-sync the Chinese docx** to match the new English §3.6 ROI provider section. Same `python-docx` approach. Pattern: walk body, for each English heading/caption that has a Chinese counterpart in `/tmp/zh_map.py` (translation map from previous round), translate; for new English body paragraphs (e.g. the three §3.6 paragraphs), add Chinese counterparts to `/tmp/zh_tr.py` and apply.
3. **Re-export the English markdown** from the canonical English docx. Script template: `/tmp/sync_md.py` (from earlier rounds). Output: `/Users/caiyunchen.3/vlma_paper_draft_v1.md`.
4. **Audit** with `/tmp/audit_en.py`. Required outcome: 0 errors, ≤ 1 false-positive warning (Table 6 "never referenced" — actually referenced as "Tables 5 and 6"; the audit regex misses compound refs).

### P1 (improves the submission but not blocking)

5. **Make a Fig. 12 for the Grounding DINO experiment** — a 2-panel figure: (a) IoU histogram (10 bins, 0.0–1.0); (b) per-part bar chart of detected ROI verification accuracy vs GT-ROI ceiling vs Full-only floor. Use `python/src/plot_main_results.py` as the matplotlib style template (TNR font, 300 dpi, white background). Insert after Fig. 11 in the English docx, mark Fig. 12 caption, then update the figure number references in body (currently none, since this is a new figure).
6. **Make a graphical abstract** if you decide to submit to MDPI *Sensors*. Single PNG, 1920×1080, the System overview (current Fig. 1) restyled is good enough.
7. **Highlights bullet** (3-5 lines) for cover letter / MDPI front matter. Already drafted material in §1 last paragraph (the "principal contributions" enumeration); rewrite into bullet form, ≤ 85 chars per line.

### P2 (would be nice; not on the critical path)

8. Add a per-seed variance band on the few-shot curve (Fig. 11) — currently only mean values plotted; the underlying CSV has per-seed columns.
9. Multi-seed repetition of the four-part Full+ROI mixed run, to give a real CI on the headline "zero-error" claim instead of Wilson upper bound. Cost: 3 × full-SFT runs on 8×H200, ~6 hours each.
10. Latency study referenced in §5.1 — currently described qualitatively; a measured "frames per second" table from a single GPU would strengthen the deployment claim.

### P3 (out of scope for this submission round)

11. End-to-end system evaluation that consumes live video and reports alarm precision / recall — explicitly deferred to future work in §5.3, do NOT add now.
12. Few-shot cross-part transfer with a small number of completion-labelled frames per new part — referenced as future work in §5.2 / §5.3.

---

## 8. Hard rules (learned the painful way over 9+ edit rounds)

These are non-negotiable. If you violate one, expect to revert from backup.

1. **Never bulk-stage with `git add -A`.** The `.gitignore` has `!python/data/<frame-dirs>/**` exceptions for LFS-tracked images; an `add -A` will try to commit hundreds of MB of frame images outside LFS and break the push. Stage by explicit path or by `python/src/*.py python/src/*.sh ...`.
2. **Never re-render the whole docx from scratch.** Always edit in place via `python-docx`. The doc currently carries the result of 12 rounds of in-place edits; a fresh render loses the embedded image data, the table styles, and the bookmark anchors.
3. **Never run a citation remap without sentinel-then-commit.** Direct `[12] → [1]` followed by `[1] → [4]` will double-translate the same number. Use `__REF_SENT_{new}__` as the intermediate token; see `/tmp/refnum.py` for the full pattern.
4. **Never `git pull` on the cloud server.** GitHub is unreachable from `116.198.70.4` (port 443 timeout). Cloud → local sync goes through rsync from the laptop. Push happens from the laptop only.
5. **Never delete a backup `_BACKUP_before_*.docx`.** They are the only escape route from a broken edit. Disk cost is ~25 MB each; we have 12 of them.
6. **Never auto-translate the Chinese mirror by simple string substitution.** The Chinese docx has its own section-level structure (theme-based) that differs from the English (chronology-based). Sync content paragraph-by-paragraph; do not assume same paragraph index → same content.
7. **Never claim a number that is not in §4 of this handoff.** If you see a percentage in the docx that does not appear in the table in §4 of this handoff, the docx is wrong, not the handoff.
8. **Never write "Hands-on" as an action class.** The action taxonomy is `{Place, Install, Tighten}` — strictly three classes. Earlier drafts used "Hands-on / Insert"; both are obsolete.
9. **Never write `Figure N.`** Use `Fig. N — Title.` (Elsevier RCIM style, em-dash, single sentence, ending period).
10. **Never run `git push` from a Cursor / Codex agent in the cloud.** It will fail with 403 (GitHub blocked). Push from the laptop, using the user's PAT-via-Keychain. If the laptop's Keychain credential expired, `printf "protocol=https\nhost=github.com\n\n" | git credential-osxkeychain erase` and retry; git will prompt for username + new PAT.

---

## 9. Live experiment state (as of 2026-06-17)

### Cloud server identity

- Host: `116.198.70.4`, port `32551`, user `root`.
- Repository path on cloud: `/mnt/workspace/users/caiyunchen/vlma`.
- Python interpreter for all experiments: `/mnt/workspace/envs/conda3/envs/starVLA_chidafeng/bin/python` (transformers 4.57.3, supports Grounding DINO).
- GPU: H200 ×8 for training; single H200 (env `CUDA_VISIBLE_DEVICES=0`) for evaluation.

### What is already trained and saved

Checkpoint locations on cloud:

```
python/output/fourpart_full_only_fullsft_v2/                   # §4.2.2 four-part Full-only
python/output/fourpart_roi_only_fullsft_v2_rerun/              # §4.2.2 four-part ROI-only
python/output/fourpart_full_roi_mixed_fullsft_v2_rerun/        # §4.2.2 four-part Full+ROI mixed (★ key)
python/output/coverx_full_only_fullsft_v2/                     # §4.2 cover-only Full-only
python/output/coverx_roi_only_fullsft_v2/                      # §4.2 cover-only ROI-only
python/output/coverx_full_roi_mixed_fullsft_v2/                # §4.2 cover-only Full+ROI mixed
python/output/multitask_assembly_plus_roi_fullsft_v1/          # §4.3.2 unified ATP + Verification
```

### Grounding DINO Tiny model on cloud

```
python/models/grounding-dino-tiny/                              # 659 MB, transferred 2026-06-17
```

### What is currently running

Background job launched 2026-06-17 ~20:50 cloud time: `bash python/src/run_grounding_dino_eval.sh`.
Log: `/tmp/gd_eval_20260617.log` on cloud.
Pipeline stages:
1. `python/src/run_grounding_dino_roi.py` — Grounding DINO Tiny pass on 112-frame 4-part test set, ~5–10 min.
2. `python/src/evaluate_model.py` — Qwen2.5-VL Full+ROI mixed re-eval on detector ROIs, ~20–30 min.
3. `python/src/compute_verification_metrics.py` — aggregate metrics, < 1 min.

Outputs land in:
- `python/data/roi_experiment_v2_4part/eval_grounding_dino/iou_summary.json` (Stage 1)
- `python/data/roi_experiment_v2_4part/eval_grounding_dino/test_roi_grounding_dino_v1.json` (Stage 1, eval JSON)
- `python/output/eval/grounding_dino_roi_provider_eval/metrics_summary.csv` (Stage 3)

### To verify completion

```bash
ssh -p 32551 root@116.198.70.4
cat /tmp/gd_eval_20260617.log | tail -50
ls -la /mnt/workspace/users/caiyunchen/vlma/python/output/eval/grounding_dino_roi_provider_eval/
cat /mnt/workspace/users/caiyunchen/vlma/python/data/roi_experiment_v2_4part/eval_grounding_dino/iou_summary.json
```

### To fill the docx after results arrive

```python
# Pseudo-script outline
from docx import Document
import json, re
gd = json.load(open('iou_summary.json'))
metrics = ...  # parse metrics_summary.csv
sub = {
    '@@IOU_MEAN@@':   f"{gd['mean_iou_detected']:.3f}",
    '@@IOU_MEDIAN@@': f"{compute_median(...):.3f}",
    '@@IOU_MIN@@':    f"{gd['min_iou_detected']:.3f}",
    '@@DET_RATE@@':   f"{gd['detection_rate']*100:.1f} %",
    '@@DET_ACC@@':    f"{metrics['accuracy']*100:.2f} %",
    '@@DET_FPR@@':    f"{metrics['fpr']*100:.2f} %",
}
doc = Document('/Users/caiyunchen.3/vlma_paper_draft_v1_en.docx')
for p in doc.paragraphs:
    for t_el in p._p.iter(qn('w:t')):
        if t_el.text and '@@' in t_el.text:
            new = t_el.text
            for k, v in sub.items():
                new = new.replace(k, v)
            t_el.text = new
# Also walk doc.tables for Table 8 row 3
doc.save(...)
```

---

## 10. Cross-language style guide (English & Chinese)

### English

- All passive voice — no "we found", "we propose". Use "is found", "is proposed", "the framework is evaluated".
- No "magic numbers" without immediate provenance — every `X %` claim must be followed by either (a) the source table reference, (b) the sample size, or (c) a Wilson CI. The exceptions are the headline numbers in the abstract.
- No `(F1)`, `(F2)`, `(D1)`, `(i)`, `(ii)` tagging in body. Sentences carry the structure, not numbered enumerators.
- Em-dashes are `—` (U+2014), not `--` or `-`. Em-dashes are never spaced when used to set off a parenthetical: `the framework — by virtue of ...` is correct.
- "Verification" and "verification" are different: capitalised when naming the mode (the Verification mode); lowercase otherwise.
- Action class names are capitalised: `Place`, `Install`, `Tighten`. Part names are capitalised as proper nouns: `Port End Cover`, `Drive Gear`, `Gear Housing`, `Thrust Block`, `Mounting Flange`, `Driven Gear`, `Capscrew`.
- Use `Full + ROI mixed` (spaces around `+`) consistently — not `Full+ROI`.
- "n = X" with spaces around the equals sign and italic n if rendering supports it.

### Chinese

- TNR for English/digits, SimSun for CJK. Set both `ascii`/`hAnsi` and `eastAsia` font slots.
- Use 半角空格 between English term and adjacent Chinese, e.g. `VLM 模型` not `VLM模型`.
- All percentages keep the space: `99.30 %` not `99.30%`.
- Section / Figure references: `4.2.2 节`, `图 8`, `表 7` (with the space).
- Proper nouns of the system remain in English: `Port End Cover`, `Full + ROI mixed`, `Grounding DINO Tiny`, etc.

---

## 11. Submission strategy decision tree (status: undecided)

The user has not yet committed to a target venue. The decision tree, summarised from earlier discussion:

- **If supervisor approves MDPI:** target `Sensors` (IF 3.5) via a Special Issue on industrial computer vision; expected acceptance window ~6 weeks (mid-Sep 2026); preferred if the goal is to have something on the CV by autumn recruiting season.
- **If supervisor insists on Elsevier:** target `Robotics and Computer-Integrated Manufacturing` (the original framing — see RCIM-style restructuring in earlier rounds); expected acceptance window 5–7 months (Dec 2026 – Feb 2027).
- **Backup for recruiting:** post on arXiv now (no review barrier; can list as preprint on CV); this is compatible with both Elsevier and MDPI submission.

The supervisor email draft is in the prior conversation; the user has not sent it as of 2026-06-17.

### If MDPI is chosen

Things to add:
- Graphical abstract (single PNG)
- MDPI Word template re-flow
- Reference style: `1. Smith, A.; Lee, B. Title. *J. Name* **2024**, *12*, 45–60.` (semicolons, italics, bold year)

### If Elsevier RCIM is chosen

Things to add:
- 3–5 Highlights (bullets, ≤ 85 chars each)
- Reference style stays as currently formatted (`[1] G. Cicirelli, ...`).

### Either way

- CRediT statement already formatted (Elsevier convention, also accepted by MDPI). Located after References.
- Declaration of competing interest already in place.

---

## 12. Files / paths you will need most often

```
# Manuscript
/Users/caiyunchen.3/vlma_paper_draft_v1_en.docx           ← edit this
/Users/caiyunchen.3/vlma_paper_draft_v1_zh.docx           ← then sync this
/Users/caiyunchen.3/vlma_paper_draft_v1.md                ← then regenerate this

# Backups
/Users/caiyunchen.3/vlma_paper_draft_v1_en_BACKUP_before_*.docx

# Code / experiments
/Users/caiyunchen.3/vlma/                                  ← local clone
github.com/Yunchen-Cai/vlma                                ← canonical repo (private)
/mnt/workspace/users/caiyunchen/vlma/                      ← cloud working tree

# Reusable editing scripts (in /tmp; copy to repo if you want them permanent)
/tmp/refnum.py            ← citation renumbering with sentinel-then-commit
/tmp/audit_en.py          ← end-of-edit consistency audit
/tmp/restructure_36.py    ← example of paragraph-insert + heading-style pattern
/tmp/sync_md.py           ← English markdown regenerator from canonical docx
/tmp/add_gd_to_docx.py    ← example of inserting Reference + caption + new para
/tmp/zh_map.py            ← heading / caption translation map (English → Chinese)
/tmp/zh_tr.py             ← body paragraph translation map (English idx → Chinese)
```

---

## 13. Hand-back checklist before declaring "done"

Before you tell the user the manuscript is ready to send:

- [ ] All `@@*@@` placeholders are gone from the English docx (grep `@@` in body and tables).
- [ ] `/tmp/audit_en.py` reports 0 errors and ≤ 1 known-false-positive warning.
- [ ] All Table N captions have a matching `<w:tbl>` element immediately following (verify via `/tmp/insert_table8.py` snippet: walk body, every caption must have a w:tbl as next non-paragraph sibling).
- [ ] All Fig. N captions are referenced at least once in body (`Fig. N` or `Figs. N and M`).
- [ ] Citation order is `[1] [2] ... [22]` by first-appearance in body, References list is in numeric order, no gaps.
- [ ] Section structure exactly matches §3 of this handoff (3.1–3.6 H2 in §3; 4.1–4.4 H2 in §4 with H3 .1/.2 each).
- [ ] Chinese docx headings / figure / table captions are in sync with English.
- [ ] English markdown is regenerated.
- [ ] Backup taken just before "done": `cp .../vlma_paper_draft_v1_en.docx .../vlma_paper_draft_v1_en_BACKUP_ready_for_<date>.docx`.

Once all boxes are checked, point the user at the canonical English docx and quit.

---

*End of handoff.*
