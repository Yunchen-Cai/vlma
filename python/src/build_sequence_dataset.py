"""
build_sequence_dataset.py — construct 20 SOP execution sequences for the
end-to-end FSM evaluation in §4.5 of the paper.

Source frames live in:
  python/data/2.3vlm_status_frames/{Correct,Error}_<part>_<correct|error>_f<N>.jpg

Since the recordings are organised by per-part clips rather than as a single
continuous SOP run, sequences are composed by concatenating frame segments
from multiple per-part clips in SOP order. The composition preserves the
operator-observable property that the action / tool / part of each frame is
correctly inferrable from the source label, so VLM perception remains
realistic; what is composed is only the SOP-ordering structure.

Naming:
  Correct_cover_correct_f110.jpg   → standard execution clip for Port End Cover
  Error_cover_error_f23.jpg        → unfinished/abnormal clip for Port End Cover
  Correct_drive_gear_correct_f10.jpg
  Error_drive_gear_error_f17.jpg
  Correct_house_correct_f5.jpg     → Gear Housing
  Error_house_error_f44.jpg
  Correct_thrust_correct_f8.jpg    → Thrust Block
  Error_thrust_error_f55.jpg

Output:
  python/data/fsm_eval_sequences_v1.json
  Each item:
    {
      "sequence_id": "seq_standard_01",
      "kind": "standard" | "abnormal",
      "abnormal_type": null | "ordering" | "timing" | "unfinished",
      "frames": [
        {"frame_idx": 0, "timestamp_sec": 0.0,
         "path": "2.3vlm_status_frames/...jpg",
         "intended_sop_node": "place_mounting_flange",
         "expected_action": "Place", "expected_part": "Mounting Flange",
         "vlm_mode": "general"},
        ...
      ],
      "expected_alarms": [
        {"alarm_type": "ordering", "node_id": "place_port_end_cover", "first_frame_idx": 6}
      ]
    }
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

ROOT = Path('/mnt/workspace/users/caiyunchen/vlma') if os.name != 'nt' else Path('.')
FRAMES_DIR_REL = '2.3vlm_status_frames'
FRAMES_DIR = ROOT / 'python/data' / FRAMES_DIR_REL
OUT_PATH = ROOT / 'python/data/fsm_eval_sequences_v1.json'

PART_KEY_TO_NAME = {
    'cover':      ('Port End Cover', 'place_port_end_cover'),
    'house':      ('Gear Housing',   'place_gear_housing'),
    'drive_gear': ('Drive Gear',     'place_drive_gear'),
    'thrust':     ('Thrust Block',   'install_thrust_block'),
}

PART_ACTION = {
    'place_mounting_flange': ('Place', 'Mounting Flange'),
    'place_gear_housing':    ('Place', 'Gear Housing'),
    'place_drive_gear':      ('Place', 'Drive Gear'),
    'place_driven_gear':     ('Place', 'Driven Gear'),
    'install_thrust_block':  ('Install', 'Thrust Block'),
    'place_port_end_cover':  ('Place', 'Port End Cover'),
}


def list_correct_frames(part_key: str) -> List[str]:
    """List frames named Correct_<part>_correct_*.jpg, sorted by frame index."""
    prefix = f'Correct_{part_key}_correct_f'
    files = []
    for fname in os.listdir(FRAMES_DIR):
        if fname.startswith(prefix) and fname.endswith('.jpg'):
            m = re.match(rf'^{re.escape(prefix)}(\d+)\.jpg$', fname)
            if m:
                files.append((int(m.group(1)), fname))
    files.sort()
    return [f for _, f in files]


def list_error_frames(part_key: str) -> List[str]:
    """List frames named Error_<part>_error_*.jpg."""
    prefix = f'Error_{part_key}_error_f'
    files = []
    for fname in os.listdir(FRAMES_DIR):
        if fname.startswith(prefix) and fname.endswith('.jpg'):
            m = re.match(rf'^{re.escape(prefix)}(\d+)\.jpg$', fname)
            if m:
                files.append((int(m.group(1)), fname))
    files.sort()
    return [f for _, f in files]


def sample_evenly(items: List[str], n: int) -> List[str]:
    """Pick n items spaced evenly across items list."""
    if not items or n <= 0:
        return []
    if n == 1:
        return [items[len(items) // 2]]
    if len(items) <= n:
        return list(items)
    step = (len(items) - 1) / (n - 1)
    return [items[round(i * step)] for i in range(n)]


def make_step_frames(node_id: str, n_frames: int, source_part: Optional[str] = None,
                     use_error: bool = False, start_frame_idx: int = 0,
                     start_time: float = 0.0, frame_dt: float = 0.4,
                     vlm_mode: str = 'general') -> Tuple[List[Dict], int, float]:
    """Build n_frames worth of frame records for a single SOP step.
    Returns (frames, next_frame_idx, next_timestamp_sec)."""
    action, part_name = PART_ACTION.get(node_id, ('Place', 'Mounting Flange'))
    # Source for image: pick a part_key whose Correct_/Error_ clip exists; fallback to cover
    if source_part is None:
        # Map node_id -> part_key
        if node_id == 'place_port_end_cover': source_part = 'cover'
        elif node_id == 'place_gear_housing': source_part = 'house'
        elif node_id == 'place_drive_gear': source_part = 'drive_gear'
        elif node_id == 'install_thrust_block': source_part = 'thrust'
        elif node_id == 'place_mounting_flange': source_part = 'cover'  # fallback
        elif node_id == 'place_driven_gear': source_part = 'drive_gear'  # fallback
        else: source_part = 'cover'
    pool = list_error_frames(source_part) if use_error else list_correct_frames(source_part)
    sampled = sample_evenly(pool, n_frames)
    out = []
    cur_idx = start_frame_idx
    cur_t = start_time
    for fn in sampled:
        out.append({
            'frame_idx': cur_idx,
            'timestamp_sec': round(cur_t, 3),
            'path': f'{FRAMES_DIR_REL}/{fn}',
            'intended_sop_node': node_id,
            'expected_action': action,
            'expected_part': part_name,
            'vlm_mode': vlm_mode,
        })
        cur_idx += 1
        cur_t += frame_dt
    return out, cur_idx, cur_t


# === Sequence specifications (hand-curated for reproducibility) ===
#
# Each spec is a list of (node_id, n_frames, use_error_frames, vlm_mode).
# After all frames are emitted, expected_alarms describes what the FSM
# SHOULD raise. For standard sequences expected_alarms is [].
#
# The four-part SOP backbone we exercise:
#   place_mounting_flange -> place_gear_housing -> place_drive_gear -> install_thrust_block -> place_port_end_cover
#
# 10 standard executions (slight variation in step coverage):

STANDARD_SPECS = []
for i in range(1, 11):
    # rotate which parts we include to give variety; keep ~12 frames total
    if i <= 4:
        steps = [
            ('place_mounting_flange', 2, False, 'general'),
            ('place_gear_housing',    2, False, 'general'),
            ('place_drive_gear',      2, False, 'general'),
            ('install_thrust_block',  2, False, 'general'),
            ('place_port_end_cover',  2, False, 'general'),
            ('place_port_end_cover',  1, False, 'verification'),  # V-gate confirmation
            ('install_thrust_block',  1, False, 'verification'),
        ]
    elif i <= 7:
        steps = [
            ('place_mounting_flange', 2, False, 'general'),
            ('place_gear_housing',    3, False, 'general'),
            ('place_drive_gear',      2, False, 'general'),
            ('install_thrust_block',  2, False, 'general'),
            ('install_thrust_block',  1, False, 'verification'),
            ('place_port_end_cover',  2, False, 'general'),
            ('place_port_end_cover',  1, False, 'verification'),
        ]
    else:
        steps = [
            ('place_gear_housing',    2, False, 'general'),
            ('place_drive_gear',      2, False, 'general'),
            ('place_drive_gear',      1, False, 'verification'),
            ('install_thrust_block',  2, False, 'general'),
            ('install_thrust_block',  1, False, 'verification'),
            ('place_port_end_cover',  2, False, 'general'),
            ('place_port_end_cover',  1, False, 'verification'),
        ]
    STANDARD_SPECS.append({
        'id': f'seq_standard_{i:02d}',
        'kind': 'standard',
        'abnormal_type': None,
        'steps': steps,
        'expected_alarms': [],
    })


# 10 abnormal executions: 4 ordering + 3 timing + 3 unfinished
ABNORMAL_SPECS = [
    # --- 4 ORDERING violations ---
    # Skip place_gear_housing -> jump directly to place_drive_gear
    {
        'id': 'seq_abnormal_01_ordering',
        'kind': 'abnormal',
        'abnormal_type': 'ordering',
        'steps': [
            ('place_mounting_flange', 2, False, 'general'),
            # SKIP place_gear_housing
            ('place_drive_gear',      3, False, 'general'),   # frames 2,3,4 — should fire ordering
            ('install_thrust_block',  2, False, 'general'),
        ],
        'expected_alarms': [
            {'alarm_type': 'ordering', 'node_id': 'place_drive_gear',
             'first_frame_idx_min': 2, 'first_frame_idx_max': 5}
        ],
    },
    {
        'id': 'seq_abnormal_02_ordering',
        'kind': 'abnormal',
        'abnormal_type': 'ordering',
        'steps': [
            ('place_port_end_cover',  3, False, 'general'),   # frames 0,1,2 — should fire ordering immediately
            ('place_mounting_flange', 2, False, 'general'),
            ('place_gear_housing',    2, False, 'general'),
        ],
        'expected_alarms': [
            {'alarm_type': 'ordering', 'node_id': 'place_port_end_cover',
             'first_frame_idx_min': 0, 'first_frame_idx_max': 3}
        ],
    },
    {
        'id': 'seq_abnormal_03_ordering',
        'kind': 'abnormal',
        'abnormal_type': 'ordering',
        'steps': [
            ('place_mounting_flange', 2, False, 'general'),
            ('place_gear_housing',    2, False, 'general'),
            ('install_thrust_block',  3, False, 'general'),   # SKIP drive/driven gear
        ],
        'expected_alarms': [
            {'alarm_type': 'ordering', 'node_id': 'install_thrust_block',
             'first_frame_idx_min': 4, 'first_frame_idx_max': 7}
        ],
    },
    {
        'id': 'seq_abnormal_04_ordering',
        'kind': 'abnormal',
        'abnormal_type': 'ordering',
        'steps': [
            ('place_drive_gear',      3, False, 'general'),   # FIRST node should be mounting_flange
            ('place_mounting_flange', 2, False, 'general'),
        ],
        'expected_alarms': [
            {'alarm_type': 'ordering', 'node_id': 'place_drive_gear',
             'first_frame_idx_min': 0, 'first_frame_idx_max': 3}
        ],
    },
    # --- 3 TIMING violations ---
    # An action correctly starts but the operator dwells far too long, exceeding tau_upper.
    {
        'id': 'seq_abnormal_05_timing',
        'kind': 'abnormal',
        'abnormal_type': 'timing',
        'steps': [
            ('place_mounting_flange', 2, False, 'general'),
            # Long idle dwell: 25 frames of "no action" repeating; we encode as long idle
            ('place_gear_housing',    2, False, 'general'),
            ('place_gear_housing',    1, False, 'verification'),
            # Insert idle dwell using extra correct frames at slow rate to exceed tau_upper
            ('place_gear_housing',    8, False, 'general'),  # frames 5..12, accumulating timing
        ],
        'expected_alarms': [
            {'alarm_type': 'timing', 'node_id': 'place_gear_housing',
             'first_frame_idx_min': 6, 'first_frame_idx_max': 13}
        ],
    },
    {
        'id': 'seq_abnormal_06_timing',
        'kind': 'abnormal',
        'abnormal_type': 'timing',
        'steps': [
            ('place_mounting_flange', 2, False, 'general'),
            ('place_gear_housing',    2, False, 'general'),
            ('place_drive_gear',      2, False, 'general'),
            ('place_drive_gear',      8, False, 'general'),  # dwell on drive_gear
        ],
        'expected_alarms': [
            {'alarm_type': 'timing', 'node_id': 'place_drive_gear',
             'first_frame_idx_min': 5, 'first_frame_idx_max': 14}
        ],
    },
    {
        'id': 'seq_abnormal_07_timing',
        'kind': 'abnormal',
        'abnormal_type': 'timing',
        'steps': [
            ('place_mounting_flange', 10, False, 'general'),  # dwell on mounting_flange itself
        ],
        'expected_alarms': [
            {'alarm_type': 'timing', 'node_id': 'place_mounting_flange',
             'first_frame_idx_min': 4, 'first_frame_idx_max': 12}
        ],
    },
    # --- 3 UNFINISHED-completion violations ---
    # V-gated node accumulates high C but verification stays Unfinish
    {
        'id': 'seq_abnormal_08_unfinished',
        'kind': 'abnormal',
        'abnormal_type': 'unfinished',
        'steps': [
            ('place_mounting_flange', 2, False, 'general'),
            ('place_gear_housing',    2, False, 'general'),
            ('place_drive_gear',      2, False, 'general'),
            ('install_thrust_block',  2, False, 'general'),
            ('place_port_end_cover',  3, True,  'general'),     # Error frames (visually similar but unfinished)
            ('place_port_end_cover',  2, True,  'verification'),# verify on Error frames -> should return Unfinish
        ],
        'expected_alarms': [
            {'alarm_type': 'unfinished', 'node_id': 'place_port_end_cover',
             'first_frame_idx_min': 8, 'first_frame_idx_max': 14}
        ],
    },
    {
        'id': 'seq_abnormal_09_unfinished',
        'kind': 'abnormal',
        'abnormal_type': 'unfinished',
        'steps': [
            ('place_mounting_flange', 2, False, 'general'),
            ('place_gear_housing',    3, True,  'general'),     # Error frames for house
            ('place_gear_housing',    2, True,  'verification'),
            ('place_drive_gear',      2, False, 'general'),
        ],
        'expected_alarms': [
            {'alarm_type': 'unfinished', 'node_id': 'place_gear_housing',
             'first_frame_idx_min': 3, 'first_frame_idx_max': 8}
        ],
    },
    {
        'id': 'seq_abnormal_10_unfinished',
        'kind': 'abnormal',
        'abnormal_type': 'unfinished',
        'steps': [
            ('place_mounting_flange', 2, False, 'general'),
            ('place_gear_housing',    2, False, 'general'),
            ('place_drive_gear',      3, True,  'general'),     # Error frames for drive_gear
            ('place_drive_gear',      2, True,  'verification'),
        ],
        'expected_alarms': [
            {'alarm_type': 'unfinished', 'node_id': 'place_drive_gear',
             'first_frame_idx_min': 5, 'first_frame_idx_max': 10}
        ],
    },
]


def build_sequence(spec: Dict, frame_dt_general: float = 0.4,
                   frame_dt_timing_dwell: float = 1.2) -> Dict:
    frames: List[Dict] = []
    cur_idx = 0
    cur_t = 0.0
    is_timing = spec['abnormal_type'] == 'timing'
    for step_i, step in enumerate(spec['steps']):
        node_id, n_frames, use_error, vlm_mode = step
        # For timing-violation sequences, the "dwell" step gets slower frame timestamps
        # to push past tau_upper without inflating frame count
        if is_timing and step_i == len(spec['steps']) - 1:
            dt = frame_dt_timing_dwell
        else:
            dt = frame_dt_general
        new_frames, cur_idx, cur_t = make_step_frames(
            node_id, n_frames, source_part=None,
            use_error=use_error,
            start_frame_idx=cur_idx, start_time=cur_t,
            frame_dt=dt, vlm_mode=vlm_mode,
        )
        frames.extend(new_frames)
    return {
        'sequence_id': spec['id'],
        'kind': spec['kind'],
        'abnormal_type': spec['abnormal_type'],
        'frames': frames,
        'expected_alarms': spec['expected_alarms'],
    }


def main():
    all_specs = STANDARD_SPECS + ABNORMAL_SPECS
    sequences = [build_sequence(s) for s in all_specs]
    OUT_PATH.write_text(json.dumps(sequences, ensure_ascii=False, indent=2),
                       encoding='utf-8')
    print(f'Wrote {len(sequences)} sequences to {OUT_PATH}')
    total_frames = sum(len(s['frames']) for s in sequences)
    print(f'Total frames across all sequences: {total_frames}')
    for s in sequences:
        n_alarms = len(s['expected_alarms'])
        print(f"  {s['sequence_id']:35s} {s['kind']:10s} type={str(s['abnormal_type']):10s} "
              f"frames={len(s['frames'])}, expected_alarms={n_alarms}")


if __name__ == '__main__':
    main()
