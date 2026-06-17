"""
measure_inference_latency.py — quantify Qwen2.5-VL-7B inference latency under
4-bit NF4 quantisation on a single GPU. Used for §5.1 latency claims.

Modes measured:
  - General mode (full frame, action/tool/part prompt)
  - Verification mode (ROI crop, finish/unfinish prompt)

For each mode: 10 warm-up calls then 100 measured calls.
Records: mean / p50 / p99 latency (ms), peak VRAM (GB), throughput (FPS).

Output: python/output/eval/latency_v1/latency_summary.json
"""
from __future__ import annotations
import json
import os
import time
from pathlib import Path

os.environ.setdefault("TRANSFORMERS_NO_TF", "1")
os.environ.setdefault("USE_TF", "0")

import torch
from PIL import Image
from transformers import AutoProcessor, Qwen2_5_VLForConditionalGeneration

ROOT = Path('/mnt/workspace/users/caiyunchen/vlma')
MODEL_DIR = ROOT / 'python/output/fourpart_full_roi_mixed_fullsft_v2_rerun'
DATA_ROOT = ROOT / 'python/data'
SPLIT_CSV = ROOT / 'python/data/roi_experiment_v2_4part/metadata/split_test_v1.csv'
OUT_DIR = ROOT / 'python/output/eval/latency_v1'
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


def load_test_samples(n: int = 20):
    """Load a small set of (full_frame_path, roi_crop_path, part) tuples."""
    import csv
    samples = []
    with open(SPLIT_CSV, encoding='utf-8') as f:
        for row in csv.DictReader(f):
            # image_path is relative to python/data/; roi_image_path is relative to
            # python/data/roi_experiment_v2_4part/
            samples.append({
                'full_path': DATA_ROOT / row['image_path'],
                'roi_path': DATA_ROOT / 'roi_experiment_v2_4part' / row['roi_image_path'],
                'part': row['part'],
            })
            if len(samples) >= n:
                break
    return samples


def build_general_message(img_path: Path):
    return [{
        "role": "user",
        "content": [
            {"type": "image", "image": str(img_path)},
            {"type": "text", "text": GENERAL_PROMPT},
        ],
    }]


def build_verify_message(img_path: Path, part: str):
    return [{
        "role": "user",
        "content": [
            {"type": "image", "image": str(img_path)},
            {"type": "text", "text": VERIFY_PROMPT_TPL.format(part=part)},
        ],
    }]


def measure_mode(mode: str, samples, model, processor, device,
                 n_warmup: int = 10, n_measure: int = 100):
    from qwen_vl_utils import process_vision_info

    print(f"\n[{mode}] warming up ({n_warmup} calls)...")
    for i in range(n_warmup):
        s = samples[i % len(samples)]
        if mode == 'general':
            msg = build_general_message(s['full_path'])
        else:
            msg = build_verify_message(s['roi_path'], s['part'])
        text = processor.apply_chat_template(msg, tokenize=False, add_generation_prompt=True)
        image_inputs, video_inputs = process_vision_info(msg)
        inputs = processor(text=[text], images=image_inputs, videos=video_inputs,
                          padding=True, return_tensors="pt").to(device)
        with torch.no_grad():
            _ = model.generate(**inputs, max_new_tokens=128, do_sample=False)
        torch.cuda.synchronize()

    print(f"[{mode}] measuring ({n_measure} calls)...")
    torch.cuda.empty_cache()
    torch.cuda.reset_peak_memory_stats()
    latencies_ms = []
    for i in range(n_measure):
        s = samples[i % len(samples)]
        if mode == 'general':
            msg = build_general_message(s['full_path'])
        else:
            msg = build_verify_message(s['roi_path'], s['part'])
        text = processor.apply_chat_template(msg, tokenize=False, add_generation_prompt=True)
        image_inputs, video_inputs = process_vision_info(msg)
        inputs = processor(text=[text], images=image_inputs, videos=video_inputs,
                          padding=True, return_tensors="pt").to(device)
        torch.cuda.synchronize()
        t0 = time.perf_counter()
        with torch.no_grad():
            _ = model.generate(**inputs, max_new_tokens=128, do_sample=False)
        torch.cuda.synchronize()
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        latencies_ms.append(elapsed_ms)
        if (i + 1) % 20 == 0:
            mean_so_far = sum(latencies_ms) / len(latencies_ms)
            print(f"  {i+1}/{n_measure}: running mean = {mean_so_far:.1f} ms")
    peak_vram_gb = torch.cuda.max_memory_allocated() / 1e9
    latencies_ms.sort()
    return {
        'mode': mode,
        'n_warmup': n_warmup,
        'n_measure': n_measure,
        'mean_ms': sum(latencies_ms) / n_measure,
        'p50_ms': latencies_ms[n_measure // 2],
        'p99_ms': latencies_ms[min(int(n_measure * 0.99), n_measure - 1)],
        'min_ms': latencies_ms[0],
        'max_ms': latencies_ms[-1],
        'peak_vram_gb': peak_vram_gb,
        'throughput_fps': 1000.0 / (sum(latencies_ms) / n_measure),
    }


def main():
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    if device != 'cuda':
        raise SystemExit("CUDA not available")

    print(f"Loading model from {MODEL_DIR}")
    processor = AutoProcessor.from_pretrained(str(MODEL_DIR))
    model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
        str(MODEL_DIR),
        torch_dtype=torch.bfloat16,
        device_map='auto',
    )
    model.eval()
    print(f"GPU: {torch.cuda.get_device_name(0)}")

    samples = load_test_samples(n=30)
    print(f"Loaded {len(samples)} sample tuples for benchmarking")

    results = {}
    results['gpu_name'] = torch.cuda.get_device_name(0)
    results['general_mode'] = measure_mode('general', samples, model, processor, device)
    results['verification_mode'] = measure_mode('verification', samples, model, processor, device)

    out_path = OUT_DIR / 'latency_summary.json'
    out_path.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding='utf-8')
    print(f"\nSaved: {out_path}")
    print()
    print("=== Latency summary ===")
    print(json.dumps(results, indent=2))


if __name__ == '__main__':
    main()
