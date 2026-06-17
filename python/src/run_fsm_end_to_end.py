"""
run_fsm_end_to_end.py — for each of 20 sequences in
python/data/fsm_eval_sequences_v1.json:
  1. Run VLM inference on each frame (General or Verification mode)
  2. Feed prediction + confidence to SOPGuidedFSM
  3. Record per-frame FSM state + alarms raised
  4. After sequence ends, compare raised alarms to expected_alarms
  5. Aggregate per-alarm-type precision, recall, latency

Output:
  python/output/eval/fsm_end_to_end_v1/sequence_results.csv  (per-frame log)
  python/output/eval/fsm_end_to_end_v1/per_alarm_metrics.csv (aggregated)
  python/output/eval/fsm_end_to_end_v1/alarm_audit.json      (per-sequence detail)
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

os.environ.setdefault("TRANSFORMERS_NO_TF", "1")
os.environ.setdefault("USE_TF", "0")

import pandas as pd
import torch
from PIL import Image
from transformers import AutoProcessor, Qwen2_5_VLForConditionalGeneration

ROOT = Path('/mnt/workspace/users/caiyunchen/vlma')
sys.path.insert(0, str(ROOT / 'python/src'))
from fsm_state_machine import SOPGuidedFSM

MODEL_DIR = ROOT / 'python/output/fourpart_full_roi_mixed_fullsft_v2_rerun'
SEQ_JSON = ROOT / 'python/data/fsm_eval_sequences_v1.json'
SOP_JSON = ROOT / 'python/data/sop_graph_gearpump.json'
DATA_ROOT = ROOT / 'python/data'
OUT_DIR = ROOT / 'python/output/eval/fsm_end_to_end_v1'
OUT_DIR.mkdir(parents=True, exist_ok=True)


GENERAL_PROMPT = (
    "You are an assembly quality inspector. Observe this frame. "
    "Identify the hand action, tool, and part. "
    "Constraint 1 — Tools: the tool must be chosen from {Hands, Hex Wrench, Screwdriver, "
    "Open End Wrench, Adjustable Wrench, Hammer}. "
    "Constraint 2 — Actions: the action must be chosen from {Install, Tighten, Place}. "
    "Constraint 3 — Parts: the part must be chosen from {Mounting Flange, Gear Housing, "
    "Thrust Block, Drive Gear, Driven Gear, Port End Cover, Capscrew}. "
    "Output ONLY in this JSON format: {\"action\": \"...\", \"tool\": \"...\", \"part\": \"...\"}."
)
VERIFY_PROMPT_TPL = (
    "You are an assembly quality inspector. This image is a cropped region around the {part}. "
    "Determine whether the assembly state is Finish or Unfinish. "
    "Output only JSON: {{\"part\": \"...\", \"verification\": \"Finish/Unfinish\"}}."
)

ALARM_MATCH_WINDOW = 5  # frames tolerance for matching expected alarm trigger


def parse_json_output(text: str) -> Dict[str, Any]:
    text = text.strip()
    m = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, flags=re.S)
    if m:
        text = m.group(1)
    m = re.search(r'\{[^{}]*\}', text)
    if m:
        text = m.group(0)
    try:
        return json.loads(text)
    except Exception:
        return {}


def vlm_call(model, processor, image_path: Path, mode: str, part: str = ''):
    """Returns (parsed, raw, confidence)."""
    if mode == 'general':
        prompt = GENERAL_PROMPT
    else:
        prompt = VERIFY_PROMPT_TPL.format(part=part)
    messages = [{
        'role': 'user',
        'content': [
            {'type': 'image', 'image': str(image_path)},
            {'type': 'text', 'text': prompt},
        ],
    }]
    prompt_text = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    img = Image.open(image_path).convert('RGB')
    inputs = processor(text=[prompt_text], images=[img], padding=True, return_tensors='pt').to(model.device)
    with torch.no_grad():
        out = model.generate(
            **inputs,
            max_new_tokens=128,
            do_sample=False,
            return_dict_in_generate=True,
            output_scores=True,
        )
    seq = out.sequences[0]
    input_len = inputs.input_ids.shape[1]
    gen_ids = seq[input_len:]
    log_probs = []
    for step, score in enumerate(out.scores):
        if step >= len(gen_ids):
            break
        token_id = gen_ids[step].item()
        log_softmax = torch.log_softmax(score[0].float(), dim=-1)
        log_probs.append(log_softmax[token_id].item())
    confidence = float(torch.tensor(sum(log_probs) / max(len(log_probs), 1)).exp().item()) if log_probs else 0.0
    decoded = processor.batch_decode([gen_ids], skip_special_tokens=True,
                                     clean_up_tokenization_spaces=False)[0].strip()
    parsed = parse_json_output(decoded)
    return parsed, decoded, confidence


def run_one_sequence(seq: Dict, model, processor, sop_json_path: Path) -> Dict:
    fsm = SOPGuidedFSM(str(sop_json_path))
    per_frame_log = []
    raised_alarms = []  # list of Alarm
    for f in seq['frames']:
        img_path = DATA_ROOT / f['path']
        try:
            parsed, raw, conf = vlm_call(model, processor, img_path,
                                          f['vlm_mode'], part=f.get('expected_part', ''))
        except Exception as e:
            parsed = {}
            raw = f'ERROR: {e}'
            conf = 0.0
        new_alarms = fsm.consume(f['frame_idx'], f['timestamp_sec'],
                                  f['vlm_mode'], parsed, conf)
        raised_alarms.extend(new_alarms)
        per_frame_log.append({
            'sequence_id': seq['sequence_id'],
            'frame_idx': f['frame_idx'],
            'timestamp_sec': f['timestamp_sec'],
            'vlm_mode': f['vlm_mode'],
            'intended_sop_node': f['intended_sop_node'],
            'expected_action': f['expected_action'],
            'expected_part': f['expected_part'],
            'pred_action': parsed.get('action', ''),
            'pred_part': parsed.get('part', ''),
            'pred_verification': parsed.get('verification', ''),
            'confidence': conf,
            'raw_output': raw[:200],
            'n_alarms_so_far': len(fsm.alarms_raised),
        })
    # Match raised alarms vs expected
    matched_expected = [False] * len(seq['expected_alarms'])
    matched_raised = [False] * len(raised_alarms)
    matches = []
    for i, exp in enumerate(seq['expected_alarms']):
        # Find the earliest raised alarm of the same type & node within window
        for j, a in enumerate(raised_alarms):
            if matched_raised[j]:
                continue
            if a.alarm_type != exp['alarm_type']:
                continue
            # Optionally also check node_id, but allow flexibility:
            if 'node_id' in exp and a.node_id != exp['node_id']:
                continue
            # Window match
            f_min = exp.get('first_frame_idx_min', exp.get('first_frame_idx', 0) - ALARM_MATCH_WINDOW)
            f_max = exp.get('first_frame_idx_max', exp.get('first_frame_idx', 0) + ALARM_MATCH_WINDOW)
            if f_min <= a.frame_idx <= f_max:
                matched_expected[i] = True
                matched_raised[j] = True
                matches.append({
                    'expected': exp,
                    'matched_at_frame': a.frame_idx,
                    'matched_score': a.score,
                    'latency_frames': a.frame_idx - exp.get('first_frame_idx', f_min),
                })
                break
    audit = {
        'sequence_id': seq['sequence_id'],
        'kind': seq['kind'],
        'abnormal_type': seq['abnormal_type'],
        'n_expected_alarms': len(seq['expected_alarms']),
        'n_raised_alarms': len(raised_alarms),
        'matched_expected': sum(matched_expected),
        'unmatched_expected': len(seq['expected_alarms']) - sum(matched_expected),
        'unmatched_raised': len(raised_alarms) - sum(matched_raised),
        'matches': matches,
        'raised_alarms_detail': [
            {'alarm_type': a.alarm_type, 'node_id': a.node_id,
             'frame_idx': a.frame_idx, 'timestamp_sec': a.timestamp_sec,
             'score': a.score, 'matched': matched_raised[j]}
            for j, a in enumerate(raised_alarms)
        ],
    }
    return {'frame_log': per_frame_log, 'audit': audit}


def aggregate_metrics(audits: List[Dict]) -> Dict:
    """Compute per-alarm-type precision, recall, median latency."""
    from collections import defaultdict
    counters = defaultdict(lambda: {'tp': 0, 'fp': 0, 'fn': 0, 'latencies': []})
    standard_false_alarms = 0
    n_standard_sequences = 0
    for a in audits:
        if a['kind'] == 'standard':
            n_standard_sequences += 1
            standard_false_alarms += a['n_raised_alarms']
            continue
        # Abnormal
        # FN per expected (unmatched expected)
        for m in a['matches']:
            t = m['expected']['alarm_type']
            counters[t]['tp'] += 1
            counters[t]['latencies'].append(m['latency_frames'])
        for exp in [e for i, e in enumerate(a.get('expected_alarms', [])) if False]:
            pass  # We'll compute FN differently below
        # FN = unmatched expected
        # Reconstruct unmatched expected via matches absence (audit['n_expected_alarms'] - audit['matched_expected'])
        # But we need per-type. Let's recompute from audit raw.
        # Build sets:
        exp_alarms = [e for e in a.get('matches', [])]  # only matched listed; we lost unmatched type info
        # Instead: read all expected from raised_alarms_detail won't tell us. We need expected_alarms in audit.
        # FIX: include expected_alarms in audit (done downstream).
    return {'counters': dict(counters),
            'n_standard_sequences': n_standard_sequences,
            'false_alarms_on_standard': standard_false_alarms}


def main():
    print('Loading sequences')
    sequences = json.loads(SEQ_JSON.read_text(encoding='utf-8'))
    total_frames = sum(len(s['frames']) for s in sequences)
    print(f'  {len(sequences)} sequences, {total_frames} total frames')

    print(f'Loading VLM model from {MODEL_DIR}')
    processor = AutoProcessor.from_pretrained(str(MODEL_DIR))
    model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
        str(MODEL_DIR),
        torch_dtype=torch.bfloat16,
        device_map='auto',
    )
    model.eval()
    print(f'GPU: {torch.cuda.get_device_name(0)}')

    all_logs = []
    all_audits = []
    t_start = time.perf_counter()
    for i, seq in enumerate(sequences):
        result = run_one_sequence(seq, model, processor, SOP_JSON)
        # Inject expected_alarms into audit for metrics
        result['audit']['expected_alarms'] = seq['expected_alarms']
        all_logs.extend(result['frame_log'])
        all_audits.append(result['audit'])
        elapsed = time.perf_counter() - t_start
        print(f'  [{i+1}/{len(sequences)}] {seq["sequence_id"]:35s} '
              f'frames={len(seq["frames"])} raised={result["audit"]["n_raised_alarms"]} '
              f'matched_exp={result["audit"]["matched_expected"]}/{result["audit"]["n_expected_alarms"]} '
              f'elapsed={elapsed:.1f}s')

    # Save per-frame CSV
    df = pd.DataFrame(all_logs)
    seq_csv = OUT_DIR / 'sequence_results.csv'
    df.to_csv(seq_csv, index=False)

    # Save audit JSON
    audit_json = OUT_DIR / 'alarm_audit.json'
    audit_json.write_text(json.dumps(all_audits, indent=2, ensure_ascii=False), encoding='utf-8')

    # Compute metrics
    from collections import defaultdict
    counters = defaultdict(lambda: {'tp': 0, 'fp': 0, 'fn': 0, 'latencies_frames': []})
    n_standard_sequences = 0
    false_alarms_on_standard = 0

    for a in all_audits:
        if a['kind'] == 'standard':
            n_standard_sequences += 1
            false_alarms_on_standard += a['n_raised_alarms']
            # All raised on standard are FP — assign to their own type counters
            for ra in a['raised_alarms_detail']:
                counters[ra['alarm_type']]['fp'] += 1
            continue
        # Abnormal: TPs from matches, FNs from unmatched expected, FPs from unmatched raised
        matched_exp_indices = set()
        for m_idx, m in enumerate(a['matches']):
            t = m['expected']['alarm_type']
            counters[t]['tp'] += 1
            counters[t]['latencies_frames'].append(m['latency_frames'])
            matched_exp_indices.add(m_idx)
        # FN per type
        for exp in a['expected_alarms'][len(a['matches']):]:
            counters[exp['alarm_type']]['fn'] += 1
        # FP per type (raised but not matched)
        for ra in a['raised_alarms_detail']:
            if not ra['matched']:
                counters[ra['alarm_type']]['fp'] += 1

    # Build metrics dataframe
    rows = []
    total_tp = total_fp = total_fn = 0
    total_lat = []
    for atype in ['ordering', 'timing', 'unfinished']:
        c = counters[atype]
        tp, fp, fn = c['tp'], c['fp'], c['fn']
        p = tp / (tp + fp) if (tp + fp) > 0 else float('nan')
        r = tp / (tp + fn) if (tp + fn) > 0 else float('nan')
        med_lat = (sorted(c['latencies_frames'])[len(c['latencies_frames']) // 2]
                   if c['latencies_frames'] else float('nan'))
        rows.append({
            'alarm_type': atype,
            'tp': tp, 'fp': fp, 'fn': fn,
            'precision': p, 'recall': r,
            'median_latency_frames': med_lat,
        })
        total_tp += tp; total_fp += fp; total_fn += fn
        total_lat.extend(c['latencies_frames'])

    rows.append({
        'alarm_type': 'TOTAL_micro',
        'tp': total_tp, 'fp': total_fp, 'fn': total_fn,
        'precision': total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else float('nan'),
        'recall': total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else float('nan'),
        'median_latency_frames': (sorted(total_lat)[len(total_lat) // 2] if total_lat else float('nan')),
    })
    rows.append({
        'alarm_type': 'FALSE_ALARMS_on_standard',
        'tp': '', 'fp': false_alarms_on_standard, 'fn': '',
        'precision': '', 'recall': false_alarms_on_standard / max(n_standard_sequences, 1),
        'median_latency_frames': '',
    })

    metrics_df = pd.DataFrame(rows)
    metrics_csv = OUT_DIR / 'per_alarm_metrics.csv'
    metrics_df.to_csv(metrics_csv, index=False)

    print()
    print('=== Per-alarm-type metrics ===')
    print(metrics_df.to_string(index=False))
    print()
    print(f'Saved:')
    print(f'  {seq_csv}')
    print(f'  {audit_json}')
    print(f'  {metrics_csv}')


if __name__ == '__main__':
    main()
