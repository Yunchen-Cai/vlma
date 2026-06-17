import csv
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path('/mnt/workspace/users/caiyunchen/vlma/python/output')
INPUTS = {
    'Full-only': ROOT / 'eval' / 'cover_full_only_eval_v2' / 'metrics_summary.csv',
    'ROI-only': ROOT / 'eval' / 'cover_roi_only_eval_v3' / 'metrics_summary.csv',
    'Full+ROI mixed': ROOT / 'eval' / 'cover_full_roi_mixed_fullsft_v1_eval' / 'metrics_summary.csv',
}
OUT_PNG = ROOT / 'fig_main_results.png'
OUT_CSV = ROOT / 'fig_main_results_table.csv'

rows = []
for model_name, path in INPUTS.items():
    if not path.exists():
        continue
    with path.open() as f:
        for row in csv.DictReader(f):
            if row['dataset'] == 'all':
                continue
            row = dict(row)
            row['model'] = model_name
            rows.append(row)

if not rows:
    raise SystemExit('No metrics files found.')

df = pd.DataFrame(rows)
for col in ['accuracy', 'f1', 'fpr', 'fnr']:
    df[col] = df[col].astype(float)

df.to_csv(OUT_CSV, index=False)

fig, axes = plt.subplots(1, 3, figsize=(14, 4))
metrics = [('accuracy', 'Accuracy'), ('f1', 'F1'), ('fpr', 'FPR')]
datasets = ['test_full_v1', 'test_roi_v1']
colors = {'test_full_v1': '#1f77b4', 'test_roi_v1': '#ff7f0e'}

for ax, (metric, title) in zip(axes, metrics):
    pivot = df.pivot(index='model', columns='dataset', values=metric).reindex(INPUTS.keys())
    x = range(len(pivot.index))
    width = 0.35
    for i, dataset in enumerate(datasets):
        if dataset not in pivot.columns:
            continue
        offset = -width / 2 if i == 0 else width / 2
        ax.bar([v + offset for v in x], pivot[dataset], width=width, label=dataset, color=colors[dataset])
    ax.set_title(title)
    ax.set_xticks(list(x))
    ax.set_xticklabels(pivot.index, rotation=15)
    ax.set_ylim(0.0, 1.05)
    ax.grid(axis='y', alpha=0.3)

axes[-1].legend()
fig.tight_layout()
fig.savefig(OUT_PNG, dpi=200, bbox_inches='tight')
print(OUT_CSV)
print(OUT_PNG)
