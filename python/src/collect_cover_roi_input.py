import argparse
import shutil
from pathlib import Path


IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
DEFAULT_SOURCES = [
    Path("python/data/2.3vlm_status_frames"),
    Path("python/data/3.14vlm_verification_frames"),
    Path("python/data/3.16test_vlm_verification_frames"),
]

UNFINISH_HINTS = (
    "incorrect",
    "wrong",
    "unfinish",
    "unfinished",
    "misalign",
    "misaligned",
    "upside",
    "bad",
    "error",
    "fault",
    "fail",
    "ng",
)
FINISH_HINTS = (
    "correct",
    "finish",
    "finished",
    "perfect",
    "ok",
)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Collect cover images into Finish/Unfinish ROI annotation folders."
    )
    parser.add_argument(
        "--source",
        action="append",
        type=Path,
        help="Source directory. Can be passed multiple times. Defaults to known VLM frame folders.",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("python/data/roi_annotation_input"),
    )
    parser.add_argument(
        "--keyword",
        default="cover",
        help="Only files whose names contain this keyword are considered.",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually copy files. Without this flag, only prints a dry-run summary.",
    )
    return parser.parse_args()


def classify(name):
    lower = name.lower()
    if any(hint in lower for hint in UNFINISH_HINTS):
        return "Unfinish"
    if any(hint in lower for hint in FINISH_HINTS):
        return "Finish"
    return None


def iter_images(sources, keyword):
    keyword = keyword.lower()
    for source in sources:
        if not source.exists():
            print(f"[missing] {source}")
            continue
        for path in sorted(source.rglob("*")):
            if not path.is_file() or path.suffix.lower() not in IMAGE_SUFFIXES:
                continue
            if keyword not in path.name.lower():
                continue
            yield source, path


def unique_destination(output_root, label, source, path):
    source_slug = source.name.replace(" ", "_")
    destination = output_root / label / f"{source_slug}__{path.name}"
    counter = 2
    while destination.exists():
        destination = (
            output_root
            / label
            / f"{source_slug}__{path.stem}_{counter}{path.suffix}"
        )
        counter += 1
    return destination


def main():
    args = parse_args()
    sources = args.source or DEFAULT_SOURCES
    stats = {"Finish": 0, "Unfinish": 0, "Skipped": 0}

    if args.execute:
        (args.output_root / "Finish").mkdir(parents=True, exist_ok=True)
        (args.output_root / "Unfinish").mkdir(parents=True, exist_ok=True)

    for source, path in iter_images(sources, args.keyword):
        label = classify(path.name)
        if label is None:
            stats["Skipped"] += 1
            print(f"[skip uncertain] {path}")
            continue

        stats[label] += 1
        destination = unique_destination(args.output_root, label, source, path)
        if args.execute:
            shutil.copy2(path, destination)
            print(f"[copy {label}] {path} -> {destination}")
        else:
            print(f"[dry {label}] {path} -> {destination}")

    print("\nSummary")
    for key, value in stats.items():
        print(f"{key}: {value}")
    if not args.execute:
        print("\nDry run only. Re-run with --execute to copy files.")


if __name__ == "__main__":
    main()
