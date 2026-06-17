import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

import torch
from PIL import Image
from torch.utils.data import Dataset
from transformers import (
    AutoProcessor,
    Qwen2_5_VLForConditionalGeneration,
    Trainer,
    TrainingArguments,
)


CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent

os.environ["HF_HOME"] = str(PROJECT_ROOT / "cache" / "huggingface")

DEFAULT_MODEL_DIR = PROJECT_ROOT / "models" / "Qwen2.5-VL-7B-Instruct"
MODEL_ID = os.environ.get("VLM_MODEL_ID", str(DEFAULT_MODEL_DIR))

DEFAULT_DATA_FILE = (
    PROJECT_ROOT / "data" / "roi_experiment_v1" / "sft" / "full_roi_mixed_sft_v1.json"
)
DATA_FILE = Path(os.environ.get("VLM_DATA_FILE", str(DEFAULT_DATA_FILE)))
IMAGE_ROOT = Path(os.environ.get("VLM_IMAGE_ROOT", str(PROJECT_ROOT / "data")))

EXPERIMENT_NAME = os.environ.get("VLM_EXPERIMENT_NAME", "roi_mixed_full_sft_v1")
OUTPUT_DIR = PROJECT_ROOT / "output" / EXPERIMENT_NAME


def env_int(name: str, default: int) -> int:
    value = os.environ.get(name)
    return int(value) if value is not None else default


def env_float(name: str, default: float) -> float:
    value = os.environ.get(name)
    return float(value) if value is not None else default


PER_DEVICE_BATCH_SIZE = env_int("VLM_PER_DEVICE_BATCH_SIZE", 1)
GRADIENT_ACCUMULATION_STEPS = env_int("VLM_GRADIENT_ACCUMULATION_STEPS", 4)
NUM_TRAIN_EPOCHS = env_float("VLM_NUM_TRAIN_EPOCHS", 4)
LEARNING_RATE = env_float("VLM_LEARNING_RATE", 2e-5)
WEIGHT_DECAY = env_float("VLM_WEIGHT_DECAY", 0.01)
WARMUP_RATIO = env_float("VLM_WARMUP_RATIO", 0.03)
LOGGING_STEPS = env_int("VLM_LOGGING_STEPS", 5)
SAVE_STEPS = env_int("VLM_SAVE_STEPS", 50)
SAVE_TOTAL_LIMIT = env_int("VLM_SAVE_TOTAL_LIMIT", 2)
MAX_GRAD_NORM = env_float("VLM_MAX_GRAD_NORM", 1.0)
DATALOADER_NUM_WORKERS = env_int("VLM_DATALOADER_NUM_WORKERS", 4)


def resolve_image_path(image_root: Path, rel_path: str) -> Path:
    candidates = [
        image_root / rel_path,
        PROJECT_ROOT / "data" / rel_path,
        PROJECT_ROOT / "data" / "roi_experiment_v1" / rel_path,
        PROJECT_ROOT / "data" / "roi_experiment_v2_4part" / rel_path,
        PROJECT_ROOT / "data" / "roi_experiment_cover_train_2p3" / rel_path,
        PROJECT_ROOT / "data" / "roi_experiment_cover_val_314" / rel_path,
        PROJECT_ROOT / "data" / "roi_experiment_cover_test_316" / rel_path,
        PROJECT_ROOT / rel_path,
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise FileNotFoundError(f"Image not found in any known location: {rel_path}")


class AssemblyDataset(Dataset):
    def __init__(self, data_file: Path, image_root: Path, processor: AutoProcessor):
        with open(data_file, "r", encoding="utf-8") as file:
            self.data = json.load(file)
        self.image_root = image_root
        self.processor = processor

    def __len__(self) -> int:
        return len(self.data)

    def __getitem__(self, idx: int) -> Dict[str, Any]:
        item = self.data[idx]

        image_list = item["image"]
        if isinstance(image_list, str):
            image_list = [image_list]
        images = [
            Image.open(resolve_image_path(self.image_root, path)).convert("RGB")
            for path in image_list
        ]

        conversations = item.get("conversations", item.get("messages"))
        text = self.processor.apply_chat_template(
            conversations,
            tokenize=False,
            add_generation_prompt=True,
        )

        inputs = self.processor(
            text=[text],
            images=images,
            padding=False,
            return_tensors="pt",
        )

        input_ids = inputs["input_ids"].squeeze(0)
        attention_mask = inputs["attention_mask"].squeeze(0)
        labels = torch.full_like(input_ids, -100)

        last_message = conversations[-1]
        if last_message["role"] == "assistant":
            assistant_content = last_message["content"]
            reply_tokens = self.processor.tokenizer(
                assistant_content,
                add_special_tokens=False,
            )["input_ids"]
            valid_len = len(reply_tokens) + 2
            if len(input_ids) > valid_len:
                labels[-valid_len:] = input_ids[-valid_len:]
            else:
                labels = input_ids.clone()

        return {
            "input_ids": input_ids,
            "attention_mask": attention_mask,
            "labels": labels,
            "pixel_values": inputs["pixel_values"],
            "image_grid_thw": inputs["image_grid_thw"],
        }


@dataclass
class RobustQwenCollator:
    processor: Any

    def __call__(self, features: List[Dict[str, Any]]) -> Dict[str, Any]:
        max_len = max(feature["input_ids"].shape[0] for feature in features)

        input_ids_list = []
        attention_mask_list = []
        labels_list = []
        pixel_values_list = []
        image_grid_thw_list = []

        pad_id = self.processor.tokenizer.pad_token_id
        if pad_id is None:
            pad_id = self.processor.tokenizer.eos_token_id

        for feature in features:
            seq_len = feature["input_ids"].shape[0]
            pad_len = max_len - seq_len

            input_ids_list.append(
                torch.cat(
                    [
                        feature["input_ids"],
                        torch.full((pad_len,), pad_id, dtype=torch.long),
                    ]
                )
            )
            attention_mask_list.append(
                torch.cat(
                    [
                        feature["attention_mask"],
                        torch.zeros((pad_len,), dtype=torch.long),
                    ]
                )
            )
            labels_list.append(
                torch.cat(
                    [
                        feature["labels"],
                        torch.full((pad_len,), -100, dtype=torch.long),
                    ]
                )
            )
            pixel_values_list.append(feature["pixel_values"])
            image_grid_thw_list.append(feature["image_grid_thw"])

        return {
            "input_ids": torch.stack(input_ids_list),
            "attention_mask": torch.stack(attention_mask_list),
            "labels": torch.stack(labels_list),
            "pixel_values": torch.cat(pixel_values_list, dim=0),
            "image_grid_thw": torch.cat(image_grid_thw_list, dim=0),
        }


def train() -> None:
    print(f"Project root: {PROJECT_ROOT}")
    print(f"Model path: {MODEL_ID}")
    print(f"Data file: {DATA_FILE}")
    print(f"Image root: {IMAGE_ROOT}")
    print(f"Output dir: {OUTPUT_DIR}")

    processor = AutoProcessor.from_pretrained(MODEL_ID, trust_remote_code=True)
    model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
        MODEL_ID,
        torch_dtype=torch.bfloat16,
        trust_remote_code=True,
    )
    model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False})

    train_dataset = AssemblyDataset(DATA_FILE, IMAGE_ROOT, processor)
    print(f"Loaded dataset with {len(train_dataset)} samples")

    training_args = TrainingArguments(
        output_dir=str(OUTPUT_DIR),
        per_device_train_batch_size=PER_DEVICE_BATCH_SIZE,
        gradient_accumulation_steps=GRADIENT_ACCUMULATION_STEPS,
        num_train_epochs=NUM_TRAIN_EPOCHS,
        learning_rate=LEARNING_RATE,
        weight_decay=WEIGHT_DECAY,
        warmup_ratio=WARMUP_RATIO,
        logging_steps=LOGGING_STEPS,
        save_strategy="steps",
        save_steps=SAVE_STEPS,
        save_total_limit=SAVE_TOTAL_LIMIT,
        eval_strategy="no",
        bf16=True,
        fp16=False,
        max_grad_norm=MAX_GRAD_NORM,
        remove_unused_columns=False,
        report_to="tensorboard",
        logging_dir=str(OUTPUT_DIR / "runs"),
        dataloader_num_workers=DATALOADER_NUM_WORKERS,
        dataloader_pin_memory=True,
        ddp_find_unused_parameters=False,
        gradient_checkpointing=True,
        save_safetensors=True,
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        data_collator=RobustQwenCollator(processor=processor),
    )

    print("Starting full-SFT training...")
    try:
        trainer.train()
    except KeyboardInterrupt:
        print("\nTraining interrupted. Saving the latest full-SFT state...")
    finally:
        trainer.save_model(str(OUTPUT_DIR))
        processor.save_pretrained(str(OUTPUT_DIR))
        print(f"Saved model and processor to: {OUTPUT_DIR}")


if __name__ == "__main__":
    train()
