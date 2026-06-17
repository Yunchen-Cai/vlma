"""
collect_confidence.py — re-run VLM evaluation on the four-part held-out test set
while recording the per-call token-level confidence ρₜ.

Confidence = exp(mean(log-prob of generated tokens))
i.e. geometric mean of teacher-forced token probabilities under the generation.

Output:
  python/output/eval/calibration_v1/predictions_with_confidence.csv
    columns: image, gt_part, pred_part, part_correct, gt_verification,
             pred_verification, verification_correct, confidence, raw_output
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Tuple

os.environ.setdefault("TRANSFORMERS_NO_TF", "1")
os.environ.setdefault("USE_TF", "0")

import pandas as pd
import torch
from PIL import Image
from transformers import AutoProcessor, Qwen2_5_VLForConditionalGeneration

ROOT = Path('/mnt/workspace/users/caiyunchen/vlma')
MODEL_DIR = ROOT / 'python/output/fourpart_full_roi_mixed_fullsft_v2_rerun'
EVAL_FILE = ROOT / 'python/data/roi_experiment_v2_4part/eval/test_roi_v1.json'
DATA_ROOT = ROOT / 'python/data'
# The test_roi_v1.json uses image paths relative to roi_experiment_v2_4part/,
# not relative to python/data/. We resolve via this prefix.
EVAL_BASE = DATA_ROOT / 'roi_experiment_v2_4part'
OUT_DIR = ROOT / 'python/output/eval/calibration_v1'
OUT_DIR.mkdir(parents=True, exist_ok=True)


def parse_json_output(text: str) -> Dict[str, Any]:
    """Best-effort parse of model output JSON."""
    text = text.strip()
    # Strip ```json fences
    m = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, flags=re.S)
    if m:
        text = m.group(1)
    # Find first {...}
    m = re.search(r'\{[^{}]*\}', text)
    if m:
        text = m.group(0)
    try:
        return json.loads(text)
    except Exception:
        return {}


def normalize(s: str) -> str:
    return (s or '').strip().lower()


def load_model():
    processor = AutoProcessor.from_pretrained(str(MODEL_DIR))
    model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
        str(MODEL_DIR),
        torch_dtype=torch.bfloat16,
        device_map='auto',
    )
    model.eval()
    return model, processor


def run_one_with_confidence(model, processor, item: Dict[str, Any]):
    """Returns: (parsed_pred, raw_text, confidence_float, image_path_used)."""
    # Build messages: rewrite image paths to absolute
    msgs = []
    for turn in item['conversations']:
        if turn['role'] != 'user':
            continue
        new_content = []
        image_path_used = None
        for c in turn['content']:
            if c.get('type') == 'image':
                rel = c['image']
                abs_path = EVAL_BASE / rel
                new_content.append({'type': 'image', 'image': str(abs_path)})
                image_path_used = str(abs_path)
            else:
                new_content.append(c)
        msgs.append({'role': 'user', 'content': new_content})

    prompt_text = processor.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)
    image_objects = []
    for c in msgs[0]['content']:
        if c.get('type') == 'image':
            image_objects.append(Image.open(c['image']).convert('RGB'))

    inputs = processor(text=[prompt_text], images=image_objects,
                      padding=True, return_tensors='pt').to(model.device)

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

    # Compute geometric-mean confidence from output_scores
    # output_scores: tuple of length n_new_tokens; each (batch, vocab)
    log_probs = []
    for step, score in enumerate(out.scores):
        if step >= len(gen_ids):
            break
        token_id = gen_ids[step].item()
        # Some tokens may be padding/EOS; include them for now
        log_softmax = torch.log_softmax(score[0].float(), dim=-1)
        log_p = log_softmax[token_id].item()
        log_probs.append(log_p)

    if log_probs:
        # confidence = exp(mean log prob)
        mean_lp = sum(log_probs) / len(log_probs)
        confidence = float(torch.tensor(mean_lp).exp().item())
    else:
        confidence = 0.0

    decoded = processor.batch_decode([gen_ids], skip_special_tokens=True,
                                     clean_up_tokenization_spaces=False)[0].strip()
    parsed = parse_json_output(decoded)
    return parsed, decoded, confidence, image_path_used


def main():
    print(f'Loading model from {MODEL_DIR}')
    model, processor = load_model()
    print(f'GPU: {torch.cuda.get_device_name(0)}')

    data = json.load(open(EVAL_FILE, encoding='utf-8'))
    print(f'Loaded {len(data)} samples from {EVAL_FILE}')

    rows = []
    for i, item in enumerate(data):
        # Extract GT
        gt = {}
        for turn in item['conversations']:
            if turn['role'] == 'assistant':
                try:
                    gt = json.loads(turn['content'])
                except Exception:
                    gt = {}
                break

        try:
            pred, raw, conf, img_path = run_one_with_confidence(model, processor, item)
        except Exception as e:
            print(f'[{i+1}/{len(data)}] FAILED: {e}')
            continue

        gt_part = gt.get('part', '')
        gt_verif = gt.get('verification', '')
        pred_part = pred.get('part', '')
        pred_verif = pred.get('verification', '')

        rows.append({
            'image': img_path,
            'gt_part': gt_part,
            'pred_part': pred_part,
            'part_correct': normalize(gt_part) == normalize(pred_part),
            'gt_verification': gt_verif,
            'pred_verification': pred_verif,
            'verification_correct': normalize(gt_verif) == normalize(pred_verif),
            'confidence': conf,
            'raw_output': raw,
        })

        if (i + 1) % 10 == 0:
            print(f'  {i+1}/{len(data)}: latest conf={conf:.3f}, '
                  f'part_correct={normalize(gt_part) == normalize(pred_part)}, '
                  f'verif_correct={normalize(gt_verif) == normalize(pred_verif)}')

    df = pd.DataFrame(rows)
    out_csv = OUT_DIR / 'predictions_with_confidence.csv'
    df.to_csv(out_csv, index=False)

    # Quick summary
    n = len(df)
    verif_acc = df['verification_correct'].mean() if n else 0
    part_acc = df['part_correct'].mean() if n else 0
    mean_conf = df['confidence'].mean() if n else 0
    print()
    print(f'=== Summary ===')
    print(f'Samples: {n}')
    print(f'Part accuracy: {part_acc:.4f}')
    print(f'Verification accuracy: {verif_acc:.4f}')
    print(f'Mean confidence: {mean_conf:.4f}')
    print(f'Saved: {out_csv}')


if __name__ == '__main__':
    main()
