import json
import os
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pandas as pd
import torch
from PIL import Image
from tqdm import tqdm

os.environ.setdefault("TRANSFORMERS_NO_TF", "1")
os.environ.setdefault("USE_TF", "0")

from transformers import AutoProcessor, Qwen2_5_VLForConditionalGeneration

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
os.environ["HF_HOME"] = str(PROJECT_ROOT / "cache" / "huggingface")

DEFAULT_MODEL_DIR = PROJECT_ROOT / "models" / "Qwen2.5-VL-7B-Instruct"
MODEL_ID = os.environ.get("VLM_MODEL_ID", str(DEFAULT_MODEL_DIR))
IMAGE_ROOT = Path(os.environ.get("VLM_IMAGE_ROOT", str(PROJECT_ROOT / "data")))
DEFAULT_EVAL_FILES = [PROJECT_ROOT / "data" / "1.26.test.json"]
eval_files_env = os.environ.get("VLM_EVAL_FILES")
EVAL_FILES = [Path(path.strip()) for path in eval_files_env.split(",") if path.strip()] if eval_files_env else DEFAULT_EVAL_FILES
EXPERIMENT_NAME = os.environ.get("VLM_EVAL_EXPERIMENT_NAME", Path(MODEL_ID).name)
OUTPUT_DIR = PROJECT_ROOT / "output" / "eval" / EXPERIMENT_NAME
MAX_NEW_TOKENS = int(os.environ.get("VLM_MAX_NEW_TOKENS", "128"))
FIELDS = ("action", "tool", "part", "phase")


def parse_json_output(text: str) -> Dict[str, Any]:
    start = text.find("{")
    end = text.rfind("}") + 1
    if start == -1 or end <= start:
        return {}
    try:
        return json.loads(text[start:end])
    except json.JSONDecodeError:
        return {}


def normalize_text(value: Any) -> str:
    return str(value or "").strip().lower()


def resolve_image_path(rel_path: str, image_root: Path) -> Path:
    candidates = [image_root / rel_path, PROJECT_ROOT / "data" / rel_path, PROJECT_ROOT / rel_path]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise FileNotFoundError(f"Image not found in any known location: {rel_path}")


def load_model() -> Tuple[Qwen2_5_VLForConditionalGeneration, AutoProcessor]:
    print(f"Project root: {PROJECT_ROOT}")
    print(f"Model path: {MODEL_ID}")
    print(f"Image root: {IMAGE_ROOT}")
    print(f"Eval files: {[str(path) for path in EVAL_FILES]}")
    print(f"Output dir: {OUTPUT_DIR}")
    processor = AutoProcessor.from_pretrained(MODEL_ID, trust_remote_code=True)
    model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
        MODEL_ID,
        dtype=torch.bfloat16,
        device_map="auto",
        trust_remote_code=True,
    )
    model.eval()
    return model, processor


def build_messages(item: Dict[str, Any], image_root: Path) -> Tuple[List[Dict[str, Any]], str]:
    conversations = item.get("conversations", item.get("messages"))
    user_message = conversations[0]
    content = []
    image_path_used = ""
    for entry in user_message["content"]:
        if entry["type"] == "image":
            rel_path = entry["image"]
            abs_path = resolve_image_path(rel_path, image_root)
            image = Image.open(abs_path).convert("RGB")
            content.append({"type": "image", "image": image})
            image_path_used = rel_path
        elif entry["type"] == "text":
            content.append({"type": "text", "text": entry["text"]})
    return [{"role": "user", "content": content}], image_path_used


def run_single_inference(model, processor, item: Dict[str, Any], image_root: Path) -> Dict[str, Any]:
    messages, image_path_used = build_messages(item, image_root)
    prompt_text = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    image_objects = [entry["image"] for entry in messages[0]["content"] if entry["type"] == "image"]
    inputs = processor(text=[prompt_text], images=image_objects, padding=True, return_tensors="pt").to(model.device)
    with torch.no_grad():
        generated_ids = model.generate(**inputs, max_new_tokens=MAX_NEW_TOKENS)
    trimmed_ids = [output_ids[len(input_ids):] for input_ids, output_ids in zip(inputs.input_ids, generated_ids)]
    decoded = processor.batch_decode(trimmed_ids, skip_special_tokens=True, clean_up_tokenization_spaces=False)[0].strip()
    prediction = parse_json_output(decoded)
    return {"image": image_path_used, "raw_output": decoded, "prediction": prediction}


def evaluate_file(model, processor, data_file: Path, image_root: Path):
    data = json.load(open(data_file, "r", encoding="utf-8"))
    rows = []
    for item in tqdm(data, desc=f"Evaluating {data_file.name}"):
        conversations = item.get("conversations", item.get("messages"))
        ground_truth = json.loads(conversations[-1]["content"])
        image_field = item["image"][0] if isinstance(item["image"], list) else item["image"]
        try:
            infer_result = run_single_inference(model, processor, item, image_root)
            pred_json = infer_result["prediction"]
            raw_output = infer_result["raw_output"]
        except Exception as exc:
            pred_json = {}
            raw_output = f"ERROR: {exc}"
            infer_result = {"image": image_field}
        row = {"dataset": data_file.name, "image": infer_result["image"], "raw_output": raw_output}
        all_correct = True
        for field in FIELDS:
            gt = normalize_text(ground_truth.get(field, ""))
            pred = normalize_text(pred_json.get(field, ""))
            correct = gt == pred
            row[f"gt_{field}"] = gt
            row[f"pred_{field}"] = pred
            row[f"{field}_correct"] = correct
            all_correct = all_correct and correct
        row["joint_correct"] = all_correct
        rows.append(row)
    df = pd.DataFrame(rows)
    summary = {"dataset": data_file.name, "samples": int(len(df)), "joint_accuracy": float(df["joint_correct"].mean()) if len(df) else 0.0}
    for field in FIELDS:
        summary[f"{field}_accuracy"] = float(df[f"{field}_correct"].mean()) if len(df) else 0.0
    return df, summary


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    model, processor = load_model()
    summaries = []
    all_frames = []
    for data_file in EVAL_FILES:
        df, summary = evaluate_file(model, processor, data_file, IMAGE_ROOT)
        summaries.append(summary)
        all_frames.append(df)
        pred_path = OUTPUT_DIR / f"{data_file.stem}_predictions.csv"
        df.to_csv(pred_path, index=False)
        print("\n" + "=" * 40)
        print(f"Dataset: {data_file.name}")
        print(f"Samples: {summary['samples']}")
        print(f"Joint accuracy: {summary['joint_accuracy'] * 100:.2f}%")
        for field in FIELDS:
            print(f"{field.title()} accuracy: {summary[f'{field}_accuracy'] * 100:.2f}%")
        print(f"Saved predictions: {pred_path}")
    summary_df = pd.DataFrame(summaries)
    summary_df.to_csv(OUTPUT_DIR / "summary.csv", index=False)
    summary_df.to_json(OUTPUT_DIR / "summary.json", orient="records", force_ascii=False, indent=2)
    if all_frames:
        pd.concat(all_frames, ignore_index=True).to_csv(OUTPUT_DIR / "all_predictions.csv", index=False)
    print("\nSaved summary:")
    print(OUTPUT_DIR / "summary.csv")
    print(OUTPUT_DIR / "summary.json")
    print(OUTPUT_DIR / "all_predictions.csv")


if __name__ == "__main__":
    main()
