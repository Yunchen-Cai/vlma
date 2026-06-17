from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from tensorboard.backend.event_processing import event_accumulator


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("run_dir")
    args = parser.parse_args()

    out_dir = Path(args.run_dir)
    if out_dir.name == "runs":
        run_dir = out_dir
        save_dir = out_dir.parent
    else:
        run_dir = out_dir / "runs"
        save_dir = out_dir

    event_file = sorted(run_dir.glob("events.out.tfevents*"))[-1]
    ea = event_accumulator.EventAccumulator(str(event_file))
    ea.Reload()

    loss_events = ea.Scalars("train/loss")
    lr_events = ea.Scalars("train/learning_rate") if "train/learning_rate" in ea.Tags().get("scalars", []) else []

    df = pd.DataFrame({
        "step": [e.step for e in loss_events],
        "wall_time": [e.wall_time for e in loss_events],
        "loss": [e.value for e in loss_events],
    })
    if lr_events:
        lr_map = {e.step: e.value for e in lr_events}
        df["learning_rate"] = df["step"].map(lr_map)

    csv_path = save_dir / "loss_curve.csv"
    png_path = save_dir / "loss_curve.png"
    df.to_csv(csv_path, index=False)

    plt.figure(figsize=(7, 4.5))
    plt.plot(df["step"], df["loss"], marker="o", linewidth=2)
    plt.title(f"Training Loss: {save_dir.name}")
    plt.xlabel("Step")
    plt.ylabel("Loss")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(png_path, dpi=180)
    print(df.to_string(index=False))
    print(csv_path)
    print(png_path)


if __name__ == "__main__":
    main()
