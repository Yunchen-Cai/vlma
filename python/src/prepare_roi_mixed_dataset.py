import argparse
import csv
import json
import random
from collections import defaultdict
from pathlib import Path

from PIL import Image


REQUIRED_COLUMNS = {
    "image_path",
    "part",
    "gt_verification",
    "hard_case",
    "x1",
    "y1",
    "x2",
    "y2",
}


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate ROI crops and single-image SFT datasets for ROI experiments."
    )
    parser.add_argument(
        "--data-root",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "data",
        help="Root used to resolve image paths from the metadata CSV.",
    )
    parser.add_argument(
        "--metadata",
        type=Path,
        required=True,
        help="ROI annotation CSV. Relative paths are resolved from data-root.",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "data" / "roi_experiment",
        help="Directory for generated crops, splits, and SFT JSON files.",
    )
    parser.add_argument("--margin", type=float, default=0.15)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--train-ratio", type=float, default=0.70)
    parser.add_argument("--val-ratio", type=float, default=0.15)
    return parser.parse_args()


def read_metadata(path):
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        missing = REQUIRED_COLUMNS.difference(reader.fieldnames or [])
        if missing:
            raise ValueError(f"Missing metadata columns: {sorted(missing)}")
        return [normalize_row(row) for row in reader]


def normalize_row(row):
    normalized = {key: (value or "").strip() for key, value in row.items()}
    normalized["gt_verification"] = normalize_verification(
        normalized["gt_verification"]
    )
    for key in ("x1", "y1", "x2", "y2"):
        normalized[key] = int(float(normalized[key]))
    return normalized


def normalize_verification(value):
    value = value.strip().lower()
    if value == "finish":
        return "Finish"
    if value == "unfinish":
        return "Unfinish"
    raise ValueError(f"Unsupported verification label: {value!r}")


def validate_rows(rows, data_root):
    errors = []
    for index, row in enumerate(rows, start=2):
        image_path = data_root / row["image_path"]
        if not image_path.exists():
            errors.append(f"line {index}: image does not exist: {image_path}")
        if row["x2"] <= row["x1"] or row["y2"] <= row["y1"]:
            errors.append(f"line {index}: invalid bounding box")
    if errors:
        raise ValueError("\n".join(errors))


def expanded_box(row, width, height, margin):
    x1, y1, x2, y2 = (row[key] for key in ("x1", "y1", "x2", "y2"))
    box_width = x2 - x1
    box_height = y2 - y1
    pad_x = round(box_width * margin)
    pad_y = round(box_height * margin)
    return (
        max(0, x1 - pad_x),
        max(0, y1 - pad_y),
        min(width, x2 + pad_x),
        min(height, y2 + pad_y),
    )


def generate_roi_crops(rows, data_root, output_root, margin):
    crop_root = output_root / "images_roi_bbox"
    for row in rows:
        source_path = data_root / row["image_path"]
        part_slug = slugify(row["part"])
        source_relative = Path(row["image_path"])
        crop_relative = Path("images_roi_bbox") / part_slug / (
            f"{source_relative.stem}_roi{source_relative.suffix}"
        )
        crop_path = output_root / crop_relative
        crop_path.parent.mkdir(parents=True, exist_ok=True)

        with Image.open(source_path) as image:
            crop = image.convert("RGB").crop(
                expanded_box(row, image.width, image.height, margin)
            )
            crop.save(crop_path)

        row["roi_image_path"] = crop_relative.as_posix()

    return crop_root


def slugify(value):
    return "_".join(value.lower().split())


def stratified_split(rows, seed, train_ratio, val_ratio):
    groups = defaultdict(list)
    for row in rows:
        key = (row["part"], row["gt_verification"], row["hard_case"])
        groups[key].append(row)

    rng = random.Random(seed)
    splits = {"train": [], "val": [], "test": []}

    for group in groups.values():
        rng.shuffle(group)
        count = len(group)
        train_end = round(count * train_ratio)
        val_end = train_end + round(count * val_ratio)
        splits["train"].extend(group[:train_end])
        splits["val"].extend(group[train_end:val_end])
        splits["test"].extend(group[val_end:])

    for split_rows in splits.values():
        rng.shuffle(split_rows)
    return splits


def write_split_csvs(splits, output_root):
    metadata_root = output_root / "metadata"
    metadata_root.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "image_path",
        "roi_image_path",
        "part",
        "gt_verification",
        "hard_case",
        "x1",
        "y1",
        "x2",
        "y2",
        "roi_type",
        "notes",
    ]
    for split_name, rows in splits.items():
        path = metadata_root / f"split_{split_name}_v1.csv"
        with path.open("w", encoding="utf-8", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(rows)


def build_sft_sample(image_path, part, verification, is_roi):
    if is_roi:
        prompt = (
            f"You are an assembly quality inspector. This image is a cropped region "
            f"around the {part}. Determine whether the assembly state is Finish or "
            'Unfinish. Output only JSON: {"part": "...", '
            '"verification": "Finish/Unfinish"}.'
        )
    else:
        prompt = (
            f"You are an assembly quality inspector. Determine whether the {part} "
            'assembly state is Finish or Unfinish. Output only JSON: {"part": "...", '
            '"verification": "Finish/Unfinish"}.'
        )

    target = json.dumps(
        {"part": part, "verification": verification}, ensure_ascii=False
    )
    return {
        "image": [image_path],
        "conversations": [
            {
                "role": "user",
                "content": [
                    {"type": "image", "image": image_path},
                    {"type": "text", "text": prompt},
                ],
            },
            {"role": "assistant", "content": target},
        ],
    }


def build_dataset(rows, mode):
    samples = []
    for row in rows:
        if mode in {"full", "mixed"}:
            samples.append(
                build_sft_sample(
                    row["image_path"],
                    row["part"],
                    row["gt_verification"],
                    is_roi=False,
                )
            )
        if mode in {"roi", "mixed"}:
            samples.append(
                build_sft_sample(
                    row["roi_image_path"],
                    row["part"],
                    row["gt_verification"],
                    is_roi=True,
                )
            )
    return samples


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)


def write_datasets(splits, output_root):
    sft_root = output_root / "sft"
    eval_root = output_root / "eval"

    write_json(sft_root / "full_sft_v1.json", build_dataset(splits["train"], "full"))
    write_json(sft_root / "roi_only_sft_v1.json", build_dataset(splits["train"], "roi"))
    write_json(
        sft_root / "full_roi_mixed_sft_v1.json",
        build_dataset(splits["train"], "mixed"),
    )

    for split_name in ("val", "test"):
        rows = splits[split_name]
        write_json(eval_root / f"{split_name}_full_v1.json", build_dataset(rows, "full"))
        write_json(eval_root / f"{split_name}_roi_v1.json", build_dataset(rows, "roi"))


def print_summary(splits, output_root):
    print(f"Generated ROI experiment data at: {output_root}")
    for split_name, rows in splits.items():
        print(f"{split_name}: {len(rows)} source images")
    print("Training samples:")
    print(f"  full-only: {len(splits['train'])}")
    print(f"  ROI-only: {len(splits['train'])}")
    print(f"  Full+ROI mixed: {len(splits['train']) * 2}")


def main():
    args = parse_args()
    rows = read_metadata(args.metadata)
    validate_rows(rows, args.data_root)
    args.output_root.mkdir(parents=True, exist_ok=True)
    generate_roi_crops(rows, args.data_root, args.output_root, args.margin)
    splits = stratified_split(rows, args.seed, args.train_ratio, args.val_ratio)
    write_split_csvs(splits, args.output_root)
    write_datasets(splits, args.output_root)
    print_summary(splits, args.output_root)


if __name__ == "__main__":
    main()
