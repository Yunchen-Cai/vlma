import csv
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path('/mnt/workspace/users/caiyunchen/vlma/python/output/eval')
OUT_PNG = ROOT.parent / 'fig_fewshot_curves.png'
OUT_CSV = ROOT.parent / 'fig_fewshot_curves.csv'

rows = []
for prefix, model in [('cover_full_only_fs', 'Full-only'), ('cover_roi_only_fs', 'ROI-only')]:
    for path in sorted(ROOT.glob(f'{prefix}*_eval/metrics_summary.csv')):
        size = int(path.parent.name.split('_fs')[-1].split('_')[0])
        with path.open() as f:
            for row in csv.DictReader(f):
                if row['dataset'] != 'test_roi_v1':
                    continue
                row = dict(row)
                row['model'] = model
                row['train_size'] = size
                rows.append(row)

if not rows:
    raise SystemExit('No few-shot metrics found.')

df = pd.DataFrame(rows)
for col in ['accuracy', 'f1', 'fpr', 'fnr']:
    df[col] = df[col].astype(float)
df['train_size'] = df['train_size'].astype(int)
df = df.sort_values(['model', 'train_size'])
df.to_csv(OUT_CSV, index=False)

fig, axes = plt.subplots(1, 2, figsize=(11, 4))
for ax, metric, title in [(axes[0], 'f1', 'Test ROI F1'), (axes[1], 'fpr', 'Test ROI FPR')]:
    for model, sub in df.groupby('model'):
        ax.plot(sub['train_size'], sub[metric], marker='o', label=model)
    ax.set_title(title)
    ax.set_xlabel('Training samples')
    ax.grid(alpha=0.3)
axes[0].set_ylim(0.0, 1.05)
axes[1].set_ylim(0.0, 1.05)
axes[1].legend()
fig.tight_layout()
fig.savefig(OUT_PNG, dpi=200, bbox_inches='tight')
print(OUT_CSV)
print(OUT_PNG)
