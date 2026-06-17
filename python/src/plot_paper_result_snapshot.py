import csv
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path("/mnt/workspace/users/caiyunchen/vlma/python/output")
INPUTS = {
    ("general_126", "General-only"): ROOT / "eval" / "general_1223_eval_126_general" / "summary.csv",
    ("general_126", "Unified mixed"): ROOT / "eval" / "multitask_general_coverx_mixed_eval_126_general" / "summary.csv",
    ("general_126", "Unified mixed x2"): ROOT / "eval" / "multitask_general_coverx_mixed_x2_eval_126_general" / "summary.csv",
    ("cover_314_plain", "Full-only"): ROOT / "eval" / "coverx_full_only_eval_314_plain" / "metrics_summary.csv",
    ("cover_314_plain", "ROI-only"): ROOT / "eval" / "coverx_roi_only_eval_314_plain" / "metrics_summary.csv",
    ("cover_314_plain", "Full+ROI mixed"): ROOT / "eval" / "coverx_full_roi_mixed_eval_314_plain" / "metrics_summary.csv",
    ("cover_314_plain", "Unified mixed"): ROOT / "eval" / "multitask_general_coverx_mixed_eval_314_plain" / "metrics_summary.csv",
    ("cover_314_plain", "Unified mixed x2"): ROOT / "eval" / "multitask_general_coverx_mixed_x2_eval_314_plain" / "metrics_summary.csv",
    ("cover_316_plain", "Full-only"): ROOT / "eval" / "coverx_full_only_eval_316_plain" / "metrics_summary.csv",
    ("cover_316_plain", "ROI-only"): ROOT / "eval" / "coverx_roi_only_eval_316_plain" / "metrics_summary.csv",
    ("cover_316_plain", "Full+ROI mixed"): ROOT / "eval" / "coverx_full_roi_mixed_eval_316_plain" / "metrics_summary.csv",
    ("cover_316_plain", "Unified mixed"): ROOT / "eval" / "multitask_general_coverx_mixed_eval_316_plain" / "metrics_summary.csv",
    ("cover_316_plain", "Unified mixed x2"): ROOT / "eval" / "multitask_general_coverx_mixed_x2_eval_316_plain" / "metrics_summary.csv",
    ("cover_316_guided_long", "Full+ROI mixed"): ROOT / "eval" / "coverx_full_roi_mixed_eval_316_guided_long" / "metrics_summary.csv",
    ("fourpart_plain", "ROI-only"): ROOT / "eval" / "fourpart_roi_only_fullsft_v2_rerun_eval_fourpart" / "metrics_summary.csv",
    ("fourpart_plain", "Full+ROI mixed"): ROOT / "eval" / "fourpart_full_roi_mixed_fullsft_v2_rerun_eval_fourpart" / "metrics_summary.csv",
}
OUT_CSV = ROOT / "paper_result_snapshot.csv"
OUT_PNG = ROOT / "paper_result_snapshot.png"


def load_rows():
    rows = []
    for (benchmark, model), path in INPUTS.items():
        if not path.exists():
            continue
        with path.open() as f:
            for row in csv.DictReader(f):
                merged = dict(row)
                if path.name == "metrics_summary.csv":
                    if row["dataset"] != "all":
                        continue
                else:
                    if row["dataset"] != "1.26.test.json":
                        continue
                    merged["accuracy"] = row["joint_accuracy"]
                merged["benchmark"] = benchmark
                merged["model"] = model
                rows.append(merged)
    return rows


def main():
    rows = load_rows()
    if not rows:
        raise SystemExit("No metrics files found.")

    df = pd.DataFrame(rows)
    for col in [
        "accuracy",
        "precision",
        "recall",
        "f1",
        "fpr",
        "fnr",
        "part_accuracy",
        "finish_accuracy",
        "unfinish_accuracy",
    ]:
        if col in df.columns:
            df[col] = df[col].astype(float)

    benchmark_order = [
        "general_126",
        "cover_314_plain",
        "cover_316_plain",
        "cover_316_guided_long",
        "fourpart_plain",
    ]
    model_order = ["General-only", "Full-only", "ROI-only", "Full+ROI mixed", "Unified mixed", "Unified mixed x2"]

    df["benchmark"] = pd.Categorical(df["benchmark"], categories=benchmark_order, ordered=True)
    df["model"] = pd.Categorical(df["model"], categories=model_order, ordered=True)
    df = df.sort_values(["benchmark", "model"])
    df.to_csv(OUT_CSV, index=False)

    plot_df = df[df["benchmark"] != "cover_316_guided_long"].copy()
    pivot = plot_df.pivot(index="benchmark", columns="model", values="accuracy")
    pivot = pivot.reindex(["cover_314_plain", "cover_316_plain", "fourpart_plain"]).dropna(how="all")
    fig, ax = plt.subplots(figsize=(10, 4.5))
    x = list(range(len(pivot.index)))
    present_models = [model for model in model_order if model in pivot.columns and model != "General-only"]
    width = 0.18
    start = -(len(present_models) - 1) / 2 * width
    offsets = {model: start + i * width for i, model in enumerate(present_models)}
    colors = {
        "Full-only": "#4C78A8",
        "ROI-only": "#F58518",
        "Full+ROI mixed": "#54A24B",
        "Unified mixed": "#E45756",
        "Unified mixed x2": "#72B7B2",
    }
    for model in model_order:
        if model not in pivot.columns or model not in offsets:
            continue
        ax.bar(
            [v + offsets[model] for v in x],
            pivot[model],
            width=width,
            label=model,
            color=colors[model],
        )
    ax.set_xticks(list(x))
    label_map = {
        "cover_314_plain": "Cover 3.14",
        "cover_316_plain": "Cover 3.16",
        "fourpart_plain": "Four-part",
    }
    ax.set_xticklabels([label_map.get(idx, idx) for idx in pivot.index], rotation=10)
    ax.set_ylabel("Accuracy")
    ax.set_ylim(0.5, 1.05)
    ax.set_title("ROI Verification Result Snapshot")
    ax.grid(axis="y", alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(OUT_PNG, dpi=200, bbox_inches="tight")
    print(OUT_CSV)
    print(OUT_PNG)


if __name__ == "__main__":
    main()
