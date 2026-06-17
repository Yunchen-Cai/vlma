import json
from pathlib import Path

import pandas as pd


def normalize_label(value):
    if pd.isna(value):
        return ""
    value = str(value).strip().lower()
    if value in {"finish", "finished", "true", "1"}:
        return "Finish"
    if value in {"unfinish", "unfinished", "false", "0"}:
        return "Unfinish"
    return str(value).strip()


def summarize(csv_path: Path):
    df = pd.read_csv(csv_path)
    df["gt_verification"] = df["gt_verification"].map(normalize_label)
    df["pred_verification"] = df["pred_verification"].map(normalize_label)

    tp = int(((df["gt_verification"] == "Finish") & (df["pred_verification"] == "Finish")).sum())
    tn = int(((df["gt_verification"] == "Unfinish") & (df["pred_verification"] == "Unfinish")).sum())
    fp = int(((df["gt_verification"] == "Unfinish") & (df["pred_verification"] == "Finish")).sum())
    fn = int(((df["gt_verification"] == "Finish") & (df["pred_verification"] == "Unfinish")).sum())

    total = len(df)
    accuracy = (tp + tn) / total if total else 0.0
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    fpr = fp / (fp + tn) if (fp + tn) else 0.0
    fnr = fn / (fn + tp) if (fn + tp) else 0.0
    part_accuracy = float(df["part_correct"].mean()) if "part_correct" in df else 0.0
    finish_accuracy = float((df[df["gt_verification"] == "Finish"]["pred_verification"] == "Finish").mean()) if len(df[df["gt_verification"] == "Finish"]) else 0.0
    unfinish_accuracy = float((df[df["gt_verification"] == "Unfinish"]["pred_verification"] == "Unfinish").mean()) if len(df[df["gt_verification"] == "Unfinish"]) else 0.0

    return {
        "dataset": csv_path.stem.replace("_predictions", ""),
        "samples": total,
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "fpr": fpr,
        "fnr": fnr,
        "part_accuracy": part_accuracy,
        "finish_accuracy": finish_accuracy,
        "unfinish_accuracy": unfinish_accuracy,
        "tp": tp,
        "tn": tn,
        "fp": fp,
        "fn": fn,
    }


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("input_dir")
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    rows = []
    for csv_path in sorted(input_dir.glob("*_predictions.csv")):
        rows.append(summarize(csv_path))

    df = pd.DataFrame(rows)
    out_csv = input_dir / "metrics_summary.csv"
    out_json = input_dir / "metrics_summary.json"
    df.to_csv(out_csv, index=False)
    out_json.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")
    print(df.to_string(index=False))
    print(out_csv)
    print(out_json)


if __name__ == "__main__":
    main()
