"""
Build perturbed-ROI evaluation datasets for the ROI-provider sensitivity study
described in §4.7 of the paper.

Reads the four-part test metadata
    `roi_experiment_v2_4part/metadata/split_test_v1.csv`
which already contains, per sample,
    image_path, roi_image_path, part, gt_verification, hard_case, x1, y1, x2, y2

For each requested perturbation tier, the original GT bounding box is jittered
deterministically (so reruns are reproducible), the perturbed ROI is cropped
from the source full-frame image, and a SFT-style eval JSON is emitted that
points to the new crop. Prompts are kept identical to `test_roi_v1.json` so
that perturbed-eval results are directly comparable to the GT-ROI numbers
reported in §4.5 Table 4.

Default tiers (matching §4.7 Table 7):
    c5, c10, c15  -- centre offset of +/-5%, +/-10%, +/-15% of ROI side length
    s10, s20      -- scale jitter of +/-10%, +/-20% of ROI side length

Outputs:
    <output-root>/eval_perturb/test_roi_perturb_<tag>_v1.json
    <output-root>/images_roi_bbox_perturb/<tag>/<part_dir>/<basename>_perturb_<tag>.jpg

Notes
-----
* Perturbations are sampled per sample with a per-sample-deterministic RNG
  (seeded by the image basename) so that re-running this script reproduces
  bit-identical crops; this keeps the sensitivity table re-verifiable.
* `direction` is sampled uniformly per sample; `magnitude` is the tier's
  nominal value (e.g. 0.10 for c10). The signed offset/scale factor is then
  `magnitude * direction`. Because direction is per-sample uniform, the
  resulting distribution has zero-mean centre offset / unit-mean scale, which
  matches the "ROI provider with bounded error" model used in the paper.
* Boxes are clamped to image bounds; if the resulting box has area <= 1 pixel
  it is rejected and the row is logged as `dropped`.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import cv2


# --------------------------------------------------------------------------- #
# Tier definitions
# --------------------------------------------------------------------------- #
# Each tier is (kind, magnitude). kind in {"centre", "scale"}.
DEFAULT_TIERS: Dict[str, Tuple[str, float]] = {
    "c5":  ("centre", 0.05),
    "c10": ("centre", 0.10),
    "c15": ("centre", 0.15),
    "s10": ("scale",  0.10),
    "s20": ("scale",  0.20),
}


# Map the human-readable "part" column in the CSV to the per-class subdir used
# under `images_roi_bbox/`. (We mirror the existing layout so audit tools work.)
PART_DIR_BY_NAME: Dict[str, str] = {
    "Drive Gear":     "drive_gear",
    "Gear Housing":   "gear_housing",
    "Port End Cover": "port_end_cover",
    "Thrust Block":   "thrust_block",
}


# Prompt template, identical to what test_roi_v1.json uses.
PROMPT_TEMPLATE = (
    "You are an assembly quality inspector. This image is a cropped region "
    "around the {part}. Determine whether the assembly state is Finish or "
    "Unfinish. Output only JSON: "
    '{{"part": "...", "verification": "Finish/Unfinish"}}.'
)


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
@dataclass
class Sample:
    image_path: str          # relative to data_root, e.g. "roi_annotation_input_v2_4part/...jpg"
    roi_image_path: str      # GT ROI crop path (kept for traceability)
    part: str                # "Drive Gear" / ...
    gt_verification: str     # "Finish" / "Unfinish"
    hard_case: str
    bbox: Tuple[int, int, int, int]   # (x1, y1, x2, y2) in pixels, GT bbox


def load_metadata(meta_csv: Path) -> List[Sample]:
    samples: List[Sample] = []
    with meta_csv.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                x1, y1, x2, y2 = (int(row["x1"]), int(row["y1"]),
                                  int(row["x2"]), int(row["y2"]))
            except (KeyError, ValueError):
                continue
            samples.append(Sample(
                image_path=row["image_path"],
                roi_image_path=row.get("roi_image_path", ""),
                part=row["part"],
                gt_verification=row["gt_verification"],
                hard_case=row.get("hard_case", ""),
                bbox=(x1, y1, x2, y2),
            ))
    return samples


def deterministic_rng(seed_str: str) -> random.Random:
    """Per-sample deterministic RNG."""
    h = hashlib.sha256(seed_str.encode("utf-8")).digest()
    seed_int = int.from_bytes(h[:8], "big", signed=False)
    return random.Random(seed_int)


def perturb_bbox(
    bbox: Tuple[int, int, int, int],
    img_w: int,
    img_h: int,
    kind: str,
    magnitude: float,
    rng: random.Random,
) -> Optional[Tuple[int, int, int, int]]:
    """Return a perturbed (x1, y1, x2, y2) or None if degenerate."""
    x1, y1, x2, y2 = bbox
    w = max(1, x2 - x1)
    h = max(1, y2 - y1)
    cx = x1 + w / 2.0
    cy = y1 + h / 2.0

    if kind == "centre":
        # Independent angle in [0, 2π) and magnitude exactly equal to `magnitude`
        # times the geometric mean of (w, h). Using an angle gives uniform
        # 2D direction; magnitude is fixed per-tier so the tier label is faithful.
        angle = rng.random() * 6.283185307179586
        radius = magnitude * ((w * h) ** 0.5)
        dx = radius * cosine(angle)
        dy = radius * sine(angle)
        new_cx = cx + dx
        new_cy = cy + dy
        new_w, new_h = w, h
    elif kind == "scale":
        # Sign chosen uniformly per sample; magnitude exact.
        sign = 1.0 if rng.random() < 0.5 else -1.0
        factor = 1.0 + sign * magnitude
        new_w = max(2.0, w * factor)
        new_h = max(2.0, h * factor)
        new_cx, new_cy = cx, cy
    else:
        raise ValueError(f"Unknown perturbation kind: {kind}")

    nx1 = int(round(new_cx - new_w / 2.0))
    ny1 = int(round(new_cy - new_h / 2.0))
    nx2 = int(round(new_cx + new_w / 2.0))
    ny2 = int(round(new_cy + new_h / 2.0))

    nx1 = max(0, min(img_w - 1, nx1))
    ny1 = max(0, min(img_h - 1, ny1))
    nx2 = max(0, min(img_w,     nx2))
    ny2 = max(0, min(img_h,     ny2))
    if nx2 - nx1 < 2 or ny2 - ny1 < 2:
        return None
    return (nx1, ny1, nx2, ny2)


def cosine(t: float) -> float:
    # Tiny dep-free wrapper so this script doesn't need numpy.
    import math
    return math.cos(t)


def sine(t: float) -> float:
    import math
    return math.sin(t)


def make_prompt_item(roi_rel_path: str, part: str, gt_verification: str) -> dict:
    """Construct one SFT-style eval item identical in shape to test_roi_v1.json."""
    return {
        "image": [roi_rel_path],
        "conversations": [
            {
                "role": "user",
                "content": [
                    {"type": "image", "image": roi_rel_path},
                    {"type": "text",  "text": PROMPT_TEMPLATE.format(part=part)},
                ],
            },
            {
                "role": "assistant",
                "content": json.dumps(
                    {"part": part, "verification": gt_verification},
                    ensure_ascii=False,
                ),
            },
        ],
    }


# --------------------------------------------------------------------------- #
# Main driver
# --------------------------------------------------------------------------- #
def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--metadata-csv", type=Path, required=True,
                   help="Path to split_test_v1.csv.")
    p.add_argument("--data-root",    type=Path, required=True,
                   help="Root directory the metadata's image_path is relative to "
                        "(e.g. /mnt/.../vlma/python/data).")
    p.add_argument("--output-root",  type=Path, required=True,
                   help="Root directory under which eval_perturb/ and "
                        "images_roi_bbox_perturb/ will be created.")
    p.add_argument("--tiers", type=str, default="",
                   help="Comma-separated subset of tier tags to generate "
                        "(default: all). Available: " + ", ".join(DEFAULT_TIERS))
    p.add_argument("--overwrite", action="store_true",
                   help="Re-crop and re-emit JSON even if files already exist.")
    return p.parse_args()


def main() -> None:
    args = parse_args()

    if args.tiers.strip():
        wanted = [t.strip() for t in args.tiers.split(",") if t.strip()]
        unknown = [t for t in wanted if t not in DEFAULT_TIERS]
        if unknown:
            raise SystemExit(f"Unknown tier(s): {unknown}; known = {list(DEFAULT_TIERS)}")
        tiers = {t: DEFAULT_TIERS[t] for t in wanted}
    else:
        tiers = DEFAULT_TIERS

    samples = load_metadata(args.metadata_csv)
    print(f"[info] loaded {len(samples)} test samples from {args.metadata_csv}")

    # Pre-compute the rel path of each output ROI per tier so we can dedupe quickly.
    crops_root = args.output_root / "images_roi_bbox_perturb"
    json_root  = args.output_root / "eval_perturb"
    crops_root.mkdir(parents=True, exist_ok=True)
    json_root.mkdir(parents=True, exist_ok=True)

    # Cache full-frame reads — most samples share frames across tiers.
    frame_cache: Dict[str, "cv2.Mat"] = {}

    for tag, (kind, magnitude) in tiers.items():
        print(f"\n=== tier {tag}: kind={kind}, magnitude={magnitude:+.2f} ===")
        out_items: List[dict] = []
        stats = Counter()

        for s in samples:
            part_dir = PART_DIR_BY_NAME.get(s.part)
            if part_dir is None:
                stats["skipped_unknown_part"] += 1
                continue

            src_abs = args.data_root / s.image_path
            if str(src_abs) not in frame_cache:
                img = cv2.imread(str(src_abs))
                if img is None:
                    stats["skipped_missing_image"] += 1
                    continue
                frame_cache[str(src_abs)] = img
            img = frame_cache[str(src_abs)]
            ih, iw = img.shape[:2]

            base = Path(s.image_path).stem  # e.g. "..._f1078"
            seed_str = f"{tag}|{s.image_path}|{s.bbox}"
            rng = deterministic_rng(seed_str)

            new_box = perturb_bbox(s.bbox, iw, ih, kind, magnitude, rng)
            if new_box is None:
                stats["dropped_degenerate"] += 1
                continue
            nx1, ny1, nx2, ny2 = new_box
            crop = img[ny1:ny2, nx1:nx2]
            if crop.size == 0:
                stats["dropped_empty_crop"] += 1
                continue

            # Output rel path mirrors images_roi_bbox/<part_dir>/<base>_perturb_<tag>.jpg
            out_rel = Path("images_roi_bbox_perturb") / tag / part_dir / f"{base}_perturb_{tag}.jpg"
            out_abs = args.output_root / out_rel
            out_abs.parent.mkdir(parents=True, exist_ok=True)
            if args.overwrite or not out_abs.exists():
                ok = cv2.imwrite(str(out_abs), crop)
                if not ok:
                    stats["dropped_imwrite_failed"] += 1
                    continue

            # Path stored in the eval JSON is relative to VLM_IMAGE_ROOT
            # (which run_roi_sensitivity_eval.sh sets to <data_root>/roi_experiment_v2_4part).
            # Therefore the path in the JSON should be relative to OUTPUT_ROOT
            # (which equals roi_experiment_v2_4part).
            out_items.append(make_prompt_item(
                roi_rel_path=str(out_rel),
                part=s.part,
                gt_verification=s.gt_verification,
            ))
            stats["written"] += 1

        # Emit JSON
        json_path = json_root / f"test_roi_perturb_{tag}_v1.json"
        json_path.write_text(json.dumps(out_items, ensure_ascii=False, indent=2),
                             encoding="utf-8")
        print(f"[tier {tag}] wrote {len(out_items)} items -> {json_path}")
        for k, v in stats.most_common():
            print(f"    {k:>26}: {v}")

    print("\n[done] all tiers built.")


if __name__ == "__main__":
    main()
