"""
run_grounding_dino_roi.py — use Grounding DINO Tiny as an open-vocabulary ROI
provider on the four-part verification test set, write detected ROI crops, and
emit IoU / detection stats.

Inputs
------
* CSV: python/data/roi_experiment_v2_4part/metadata/split_test_v1.csv
  Columns used: image_path, part, gt_verification, x1, y1, x2, y2
* Grounding DINO Tiny weights: python/models/grounding-dino-tiny/
* Image root: python/data/

Outputs
-------
* python/data/roi_experiment_v2_4part/eval_grounding_dino/
    iou_per_sample.csv          per-image IoU + detected box + score
    iou_summary.json            aggregate IoU stats and detection rate
    test_roi_grounding_dino_v1.json   SFT-style eval JSON for evaluate_model.py
* python/data/roi_experiment_v2_4part/images_roi_bbox_grounding_dino/<part>/<basename>_roi.jpg
    Detected ROI crops (10 % margin, matching the GT-ROI preprocessing
    described in §3.3 of the paper)

Notes
-----
* For each row we issue a single text prompt: the part name in lowercase.
  Grounding DINO is run with box_threshold=0.25 and text_threshold=0.20 (the
  HuggingFace defaults). If multiple boxes match, the highest-score box is
  kept; if no box matches, we fall back to the full frame and log a detection
  failure (so the downstream eval still has one sample per row).
* IoU is reported only when a detection is found. The detection rate
  (fraction of rows with at least one detection) is reported separately.
* The output JSON mirrors test_roi_v1.json so that evaluate_model.py can be
  rerun directly against the detector-produced ROI crops.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
from pathlib import Path
from typing import Dict, List, Tuple

import torch
from PIL import Image
from transformers import AutoProcessor, AutoModelForZeroShotObjectDetection


def iou(box_a: Tuple[float, float, float, float],
        box_b: Tuple[float, float, float, float]) -> float:
    ax1, ay1, ax2, ay2 = box_a
    bx1, by1, bx2, by2 = box_b
    inter_x1 = max(ax1, bx1)
    inter_y1 = max(ay1, by1)
    inter_x2 = min(ax2, bx2)
    inter_y2 = min(ay2, by2)
    if inter_x2 <= inter_x1 or inter_y2 <= inter_y1:
        return 0.0
    inter = (inter_x2 - inter_x1) * (inter_y2 - inter_y1)
    area_a = max(0.0, ax2 - ax1) * max(0.0, ay2 - ay1)
    area_b = max(0.0, bx2 - bx1) * max(0.0, by2 - by1)
    union = area_a + area_b - inter
    if union <= 0:
        return 0.0
    return inter / union


def expand_box(box: Tuple[float, float, float, float],
               image_size: Tuple[int, int],
               margin_frac: float = 0.10) -> Tuple[int, int, int, int]:
    """Expand box by margin_frac of the box's longer side on each side,
    clamped to image bounds. Matches the §3.3 GT-ROI preprocessing."""
    x1, y1, x2, y2 = box
    w = x2 - x1
    h = y2 - y1
    side = max(w, h)
    margin = side * margin_frac
    img_w, img_h = image_size
    new_x1 = int(max(0.0, x1 - margin))
    new_y1 = int(max(0.0, y1 - margin))
    new_x2 = int(min(float(img_w), x2 + margin))
    new_y2 = int(min(float(img_h), y2 + margin))
    return new_x1, new_y1, new_x2, new_y2


def part_to_prompt(part: str) -> str:
    """Return the Grounding DINO text prompt for a part name.

    Grounding DINO expects lowercase, period-terminated prompts.
    """
    return f"{part.lower()}."


def make_sft_sample(image_relpath: str, part: str, gt_verification: str) -> Dict:
    """Mirror the schema used by python/data/roi_experiment_v2_4part/eval/test_roi_v1.json:
    {"image": [path],
     "conversations": [
       {"role":"user",      "content": [{"type":"image","image":path}, {"type":"text","text":...}]},
       {"role":"assistant", "content": "{\"part\":\"...\",\"verification\":\"Finish/Unfinish\"}"}
     ]}
    """
    user_text = (
        f"You are an assembly quality inspector. This image is a cropped region around the "
        f"{part}. Determine whether the assembly state is Finish or Unfinish. "
        f"Output only JSON: {{\"part\": \"...\", \"verification\": \"Finish/Unfinish\"}}."
    )
    gt_content = json.dumps({"part": part, "verification": gt_verification}, ensure_ascii=False)
    return {
        "image": [image_relpath],
        "conversations": [
            {
                "role": "user",
                "content": [
                    {"type": "image", "image": image_relpath},
                    {"type": "text", "text": user_text},
                ],
            },
            {"role": "assistant", "content": gt_content},
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--csv",
        default="python/data/roi_experiment_v2_4part/metadata/split_test_v1.csv",
    )
    parser.add_argument(
        "--image-root",
        default="python/data",
        help="Prefix to prepend to image_path in the CSV.",
    )
    parser.add_argument(
        "--model-dir",
        default="python/models/grounding-dino-tiny",
    )
    parser.add_argument(
        "--out-dir",
        default="python/data/roi_experiment_v2_4part/eval_grounding_dino",
    )
    parser.add_argument(
        "--crop-dir",
        default="python/data/roi_experiment_v2_4part/images_roi_bbox_grounding_dino",
    )
    parser.add_argument("--box-threshold", type=float, default=0.25)
    parser.add_argument("--text-threshold", type=float, default=0.20)
    parser.add_argument("--margin-frac", type=float, default=0.10)
    parser.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    args = parser.parse_args()

    repo_root = Path.cwd()
    csv_path = repo_root / args.csv
    image_root = repo_root / args.image_root
    model_dir = repo_root / args.model_dir
    out_dir = repo_root / args.out_dir
    crop_dir = repo_root / args.crop_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    crop_dir.mkdir(parents=True, exist_ok=True)

    print(f"[gd-roi] loading model from {model_dir} on {args.device}")
    processor = AutoProcessor.from_pretrained(str(model_dir))
    model = AutoModelForZeroShotObjectDetection.from_pretrained(str(model_dir)).to(args.device)
    model.eval()

    rows: List[Dict] = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    print(f"[gd-roi] loaded {len(rows)} test rows from {csv_path}")

    per_sample_records: List[Dict] = []
    sft_samples: List[Dict] = []
    detection_count = 0
    iou_values: List[float] = []
    failures: List[str] = []

    for idx, row in enumerate(rows):
        rel_img = row["image_path"]
        part = row["part"]
        gt_finish = row["gt_verification"]
        x1, y1, x2, y2 = (float(row[k]) for k in ("x1", "y1", "x2", "y2"))

        abs_img = image_root / rel_img
        if not abs_img.exists():
            failures.append(f"missing image: {abs_img}")
            continue

        image = Image.open(abs_img).convert("RGB")
        img_w, img_h = image.size

        text_prompt = part_to_prompt(part)
        inputs = processor(images=image, text=text_prompt, return_tensors="pt").to(args.device)
        with torch.no_grad():
            outputs = model(**inputs)

        target_sizes = torch.tensor([image.size[::-1]], device=args.device)  # (H, W)
        results = processor.post_process_grounded_object_detection(
            outputs,
            inputs.input_ids,
            threshold=args.box_threshold,
            text_threshold=args.text_threshold,
            target_sizes=target_sizes,
        )[0]
        boxes = results["scores"].detach().cpu().tolist(), results["boxes"].detach().cpu().tolist()
        scores, det_boxes = boxes
        # Sort by score desc
        if scores:
            ranked = sorted(zip(scores, det_boxes), key=lambda x: -x[0])
            best_score, best_box = ranked[0]
            detection_count += 1
            iou_val = iou(tuple(best_box), (x1, y1, x2, y2))
            iou_values.append(iou_val)
            crop_x1, crop_y1, crop_x2, crop_y2 = expand_box(
                tuple(best_box), (img_w, img_h), margin_frac=args.margin_frac
            )
            crop = image.crop((crop_x1, crop_y1, crop_x2, crop_y2))
            crop_subdir = crop_dir / part.lower().replace(" ", "_")
            crop_subdir.mkdir(parents=True, exist_ok=True)
            basename = Path(rel_img).stem
            crop_path = crop_subdir / f"{basename}_grounding_dino_roi.jpg"
            crop.save(crop_path, quality=92)
            rel_crop = crop_path.relative_to(image_root).as_posix()
            sft_samples.append(make_sft_sample(rel_crop, part, gt_finish))
            per_sample_records.append(
                {
                    "image_path": rel_img,
                    "part": part,
                    "gt_verification": gt_finish,
                    "gt_x1": int(x1), "gt_y1": int(y1), "gt_x2": int(x2), "gt_y2": int(y2),
                    "det_x1": float(best_box[0]), "det_y1": float(best_box[1]),
                    "det_x2": float(best_box[2]), "det_y2": float(best_box[3]),
                    "det_score": float(best_score),
                    "iou": iou_val,
                    "crop_path": rel_crop,
                    "detected": True,
                }
            )
        else:
            # Fallback: use full frame so downstream eval still has a sample
            crop_subdir = crop_dir / part.lower().replace(" ", "_")
            crop_subdir.mkdir(parents=True, exist_ok=True)
            basename = Path(rel_img).stem
            crop_path = crop_subdir / f"{basename}_grounding_dino_fallback.jpg"
            image.save(crop_path, quality=92)
            rel_crop = crop_path.relative_to(image_root).as_posix()
            sft_samples.append(make_sft_sample(rel_crop, part, gt_finish))
            per_sample_records.append(
                {
                    "image_path": rel_img,
                    "part": part,
                    "gt_verification": gt_finish,
                    "gt_x1": int(x1), "gt_y1": int(y1), "gt_x2": int(x2), "gt_y2": int(y2),
                    "det_x1": 0.0, "det_y1": 0.0,
                    "det_x2": float(img_w), "det_y2": float(img_h),
                    "det_score": 0.0,
                    "iou": 0.0,
                    "crop_path": rel_crop,
                    "detected": False,
                }
            )

        if (idx + 1) % 10 == 0 or (idx + 1) == len(rows):
            mean_iou = sum(iou_values) / max(len(iou_values), 1)
            print(
                f"[gd-roi] {idx + 1:>3d}/{len(rows)} processed, "
                f"detect={detection_count}, mean IoU(detected)={mean_iou:.3f}"
            )

    # Persist per-sample CSV
    csv_out = out_dir / "iou_per_sample.csv"
    with open(csv_out, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "image_path", "part", "gt_verification",
                "gt_x1", "gt_y1", "gt_x2", "gt_y2",
                "det_x1", "det_y1", "det_x2", "det_y2",
                "det_score", "iou", "crop_path", "detected",
            ],
        )
        writer.writeheader()
        writer.writerows(per_sample_records)
    print(f"[gd-roi] wrote per-sample CSV: {csv_out}")

    # Per-part aggregate
    part_stats: Dict[str, Dict[str, float]] = {}
    for rec in per_sample_records:
        p = rec["part"]
        bucket = part_stats.setdefault(p, {"n": 0, "detected": 0, "iou_sum": 0.0, "iou_count": 0})
        bucket["n"] += 1
        if rec["detected"]:
            bucket["detected"] += 1
            bucket["iou_sum"] += rec["iou"]
            bucket["iou_count"] += 1
    for p in part_stats:
        bucket = part_stats[p]
        bucket["detection_rate"] = bucket["detected"] / max(bucket["n"], 1)
        bucket["mean_iou_detected"] = bucket["iou_sum"] / max(bucket["iou_count"], 1)

    # Summary JSON
    summary = {
        "n_rows": len(rows),
        "n_processed": len(per_sample_records),
        "n_detected": detection_count,
        "detection_rate": detection_count / max(len(per_sample_records), 1),
        "mean_iou_detected": sum(iou_values) / max(len(iou_values), 1),
        "min_iou_detected": min(iou_values) if iou_values else 0.0,
        "max_iou_detected": max(iou_values) if iou_values else 0.0,
        "iou_histogram_bins": [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
        "iou_histogram_counts": _histogram(iou_values),
        "per_part": part_stats,
        "box_threshold": args.box_threshold,
        "text_threshold": args.text_threshold,
        "margin_frac": args.margin_frac,
        "failures": failures,
    }
    summary_path = out_dir / "iou_summary.json"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[gd-roi] wrote summary: {summary_path}")
    print(json.dumps(
        {k: v for k, v in summary.items() if k not in ("iou_histogram_counts", "per_part", "failures")},
        ensure_ascii=False, indent=2,
    ))

    # SFT-style eval JSON
    sft_path = out_dir / "test_roi_grounding_dino_v1.json"
    sft_path.write_text(json.dumps(sft_samples, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[gd-roi] wrote eval JSON: {sft_path}")


def _histogram(values: List[float]) -> List[int]:
    """10-bin histogram on [0,1]."""
    bins = [0] * 10
    for v in values:
        if v >= 1.0:
            bins[-1] += 1
        elif v <= 0.0:
            bins[0] += 1
        else:
            bins[int(v * 10)] += 1
    return bins


if __name__ == "__main__":
    main()
