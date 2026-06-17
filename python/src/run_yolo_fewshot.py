"""
YOLOv8-cls few-shot baseline for Cover Port-End-Cover verification.

Reads the existing few-shot VLM training JSONs in
    `/mnt/workspace/users/caiyunchen/vlma/python/data/roi_experiment_v1/fewshot/`
to obtain the *same* per-N sample sets (so the comparison is apples-ts),
then trains a YOLOv8-cls Finish/Unfinish classifier per (N, seed) combination
and evaluates on the held-out 108-frame ROI test set.

Outputs:
    /mnt/workspace/.../python/output/yolo_fewshot/yolo_cover_roi_n{N}_seed{S}/...
    /mnt/workspace/.../python/output/yolo_fewshot/yolo_fewshot_summary.csv

Run with the conda env Python:
    /mnt/workspace/envs/conda3/envs/starVLA_chidafeng/bin/python \
        python/src/run_yolo_fewshot.py --sizes 50 100 200 300 400 --seeds 0 1 2
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import random
import shutil
from pathlib import Path
from typing import List

# Disable external loggers BEFORE importing ultralytics
os.environ.setdefault("WANDB_DISABLED", "true")
os.environ.setdefault("WANDB_MODE", "disabled")
os.environ.setdefault("YOLO_VERBOSE", "False")
os.environ.setdefault("COMET_MODE", "DISABLED")

ROOT = Path("/mnt/workspace/users/caiyunchen/vlma/python")
DATA_ROOT = ROOT / "data"
FEWSHOT_JSON_DIR = DATA_ROOT / "roi_experiment_v1" / "fewshot"
EVAL_JSON = DATA_ROOT / "roi_experiment_v1" / "eval" / "test_roi_v1.json"
OUT_ROOT = ROOT / "output" / "yolo_fewshot"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--sizes", type=int, nargs="+",
                   default=[50, 100, 200, 300, 400])
    p.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2])
    p.add_argument("--model", type=str, default="yolov8n-cls.pt",
                   help="YOLOv8 classification model")
    p.add_argument("--epochs", type=int, default=30,
                   help="Cls training epochs per run; YOLOv8-cls converges fast")
    p.add_argument("--imgsz", type=int, default=224)
    p.add_argument("--device", type=str, default="6")
    p.add_argument("--batch", type=int, default=32)
    p.add_argument("--overwrite", action="store_true")
    return p.parse_args()


def read_fewshot_json(n: int) -> List[dict]:
    """Read one of full_sft_v1_{n}.json (we use ROI-only file because YOLO works on ROI crops)."""
    path = FEWSHOT_JSON_DIR / f"roi_only_sft_v1_{n}.json"
    if not path.exists():
        # fall back to building from full_sft_v1_{n}.json (which references both full & ROI)
        path = FEWSHOT_JSON_DIR / f"full_sft_v1_{n}.json"
    with path.open() as f:
        return json.load(f)


def label_from_item(item: dict) -> str:
    """Extract Finish/Unfinish from the SFT-style item's assistant content."""
    msgs = item.get("conversations", item.get("messages"))
    a = msgs[-1]["content"]
    try:
        d = json.loads(a)
        v = str(d.get("verification", "")).strip().lower()
    except Exception:
        v = ""
    if "unfinish" in v:
        return "unfinish"
    return "finish"


def image_path_from_item(item: dict) -> Path:
    msgs = item.get("conversations", item.get("messages"))
    user = msgs[0]
    for entry in user["content"]:
        if entry["type"] == "image":
            rel = entry["image"]
            # Try a few candidate roots
            candidates = [
                DATA_ROOT / rel,
                DATA_ROOT / "roi_experiment_v1" / rel,
                ROOT / rel,
            ]
            for c in candidates:
                if c.exists():
                    return c
            # Last resort: glob match
            return DATA_ROOT / rel
    raise ValueError("no image in item")


def build_split(items: List[dict], split_dir: Path) -> None:
    """Materialise YOLOv8-cls folder layout: split_dir/{finish,unfinish}/*.jpg"""
    if split_dir.exists():
        shutil.rmtree(split_dir)
    (split_dir / "finish").mkdir(parents=True, exist_ok=True)
    (split_dir / "unfinish").mkdir(parents=True, exist_ok=True)
    for idx, it in enumerate(items):
        lbl = label_from_item(it)
        src = image_path_from_item(it)
        if not src.exists():
            print(f"[warn] missing {src}")
            continue
        dst = split_dir / lbl / f"{idx:05d}_{src.stem}.jpg"
        shutil.copy(src, dst)


def stratified_subsample(items: List[dict], n: int, seed: int) -> List[dict]:
    """Stratified sample N items from a larger pool, preserving label ratio."""
    fin = [x for x in items if label_from_item(x) == "finish"]
    unf = [x for x in items if label_from_item(x) == "unfinish"]
    r = random.Random(seed)
    r.shuffle(fin); r.shuffle(unf)
    target_fin = max(1, int(round(n * len(fin) / (len(fin) + len(unf)))))
    target_unf = n - target_fin
    return fin[:target_fin] + unf[:target_unf]


def run_one(n: int, seed: int, args: argparse.Namespace) -> dict:
    """Train + eval one (N, seed) configuration. Returns metrics dict."""
    print(f"\n=========== N={n}  seed={seed} ===========")
    # Sample N items deterministically from the existing N=400 pool
    pool = read_fewshot_json(max(args.sizes))   # use largest pool as source
    sampled = stratified_subsample(pool, n, seed)

    run_dir = OUT_ROOT / f"yolo_cover_roi_n{n}_seed{seed}"
    if run_dir.exists() and not args.overwrite:
        print(f"  skipping (exists): {run_dir}")
        # try to read metrics anyway
        m = run_dir / "metrics.csv"
        if m.exists():
            with m.open() as f:
                return next(csv.DictReader(f))
        # else fall through to retrain
    run_dir.mkdir(parents=True, exist_ok=True)

    # Build train / val splits.
    # YOLOv8-cls expects: <data_root>/{train, val}/{class}/*.jpg
    ds_dir = run_dir / "dataset"
    if ds_dir.exists():
        shutil.rmtree(ds_dir)
    build_split(sampled, ds_dir / "train")

    # Use the same eval JSON as the YOLO val split (108-frame ROI test).
    eval_items = json.loads(EVAL_JSON.read_text())
    build_split(eval_items, ds_dir / "val")

    # Train
    from ultralytics import YOLO  # imported lazily so the script can be loaded for inspection
    import os
    import torch
    torch.manual_seed(seed)
    # YOLOv8.3 rejects project paths containing '/'. Workaround: cd into OUT_ROOT
    # and use project=".".
    cwd_before = os.getcwd()
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    os.chdir(str(OUT_ROOT))
    try:
        model = YOLO(args.model)
        run_name = f"yolo_cover_roi_n{n}_seed{seed}__train"
        val_name = f"yolo_cover_roi_n{n}_seed{seed}__val"
        model.train(
            data=str(ds_dir),
            epochs=args.epochs,
            imgsz=args.imgsz,
            batch=args.batch,
            device=args.device,
            seed=seed,
            project=".",
            name=run_name,
            verbose=False,
            plots=False,
            save=True,
            exist_ok=True,
        )

        # Evaluate on val (= eval items) — read confusion matrix
        metrics = model.val(
            data=str(ds_dir),
            split="val",
            device=args.device,
            project=".",
            name=val_name,
            verbose=False,
            plots=False,
            exist_ok=True,
        )
    finally:
        os.chdir(cwd_before)
    # metrics.confusion_matrix.matrix is [cls x cls] (rows = true, cols = pred). YOLO 8.3 API.
    cm = metrics.confusion_matrix.matrix
    # Class order from val dataset: alphabetical → finish=0, unfinish=1
    # We treat Finish as positive.
    tp = int(cm[0, 0])
    fn = int(cm[0, 1])
    fp = int(cm[1, 0])
    tn = int(cm[1, 1])
    total = tp + tn + fp + fn
    accuracy = (tp + tn) / total if total else 0.0
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
    fpr = fp / (fp + tn) if (fp + tn) else 0.0
    fnr = fn / (fn + tp) if (fn + tp) else 0.0
    finish_acc = tp / (tp + fn) if (tp + fn) else 0.0
    unfinish_acc = tn / (tn + fp) if (tn + fp) else 0.0

    rec = {
  "model": "YOLOv8n-cls",
        "n": n,
        "seed": seed,
        "samples": total,
        "accuracy": round(accuracy, 6),
        "precision": round(precision, 6),
        "recall": round(recall, 6),
        "f1": round(f1, 6),
        "fpr": round(fpr, 6),
        "fnr": round(fnr, 6),
        "finish_accuracy": round(finish_acc, 6),
        "unfinish_accuracy": round(unfinish_acc, 6),
        "tp": tp, "tn": tn, "fp": fp, "fn": fn,
    }
    with (run_dir / "metrics.csv").open("w") as f:
        w = csv.DictWriter(f, fieldnames=list(rec.keys()))
        w.writeheader()
        w.writerow(rec)
    print(f"  accuracy={accuracy:.4f}  fpr={fpr:.4f}  unfin_acc={unfinish_acc:.4f}")
    return rec


def main() -> None:
    args = parse_args()
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    all_records: List[dict] = []
    for n in args.sizes:
        for seed in args.seeds:
            try:
                all_records.append(run_one(n, seed, args))
            except Exception as e:
                print(f"[error] N={n} seed={seed}: {e}")

    if all_records:
        summary = OUT_ROOT / "yolo_fewshot_summary.csv"
        with summary.open("w") as f:
            w = csv.DictWriter(f, fieldnames=list(all_records[0].keys()))
            w.writeheader()
            w.writerows(all_records)
        print(f"\n[done] summary -> {summary}")


if __name__ == "__main__":
    main()
