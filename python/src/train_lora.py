import os
import json
import torch
from pathlib import Path  # 新增：用于自动管理路径
from torch.utils.data import Dataset
from torch.utils.data import random_split
from transformers import (
    Qwen2_5_VLForConditionalGeneration,
    AutoProcessor,
    TrainingArguments,
    Trainer,
    EarlyStoppingCallback,
    BitsAndBytesConfig
)
from peft import LoraConfig, get_peft_model, TaskType, prepare_model_for_kbit_training
from PIL import Image
from dataclasses import dataclass
from typing import Dict, List, Any
import numpy as np
# ================= 动态路径配置 (核心修改) =================
# 获取当前脚本所在目录 (D:\vlm_assembly\src)
CURRENT_DIR = Path(__file__).resolve().parent
# 获取项目根目录 (D:\vlm_assembly)
PROJECT_ROOT = CURRENT_DIR.parent

# 1. 缓存路径
os.environ["HF_HOME"] = str(PROJECT_ROOT / "cache" / "huggingface")

# 2. 模型与数据路径
# 假设模型还在 cache 里，或者您可以把它移到 models 文件夹
DEFAULT_MODEL_DIR = PROJECT_ROOT / "models" / "Qwen2.5-VL-7B-Instruct"
MODEL_ID = os.environ.get("VLM_MODEL_ID", str(DEFAULT_MODEL_DIR))

# 自动定位 JSON 文件
DEFAULT_DATA_FILE = (
    PROJECT_ROOT / "data" / "roi_experiment_v1" / "sft" / "full_roi_mixed_sft_v1.json"
)
DATA_FILE = Path(os.environ.get("VLM_DATA_FILE", str(DEFAULT_DATA_FILE)))
# 自动定位图片根目录
IMAGE_ROOT = PROJECT_ROOT / "data"

# 3. 输出路径 (每次实验建议改一下版本号，如 v1, v2)
EXPERIMENT_NAME = os.environ.get(
    "VLM_EXPERIMENT_NAME", "roi_mixed_full_roi_finetune_v1"
)
OUTPUT_DIR = PROJECT_ROOT / "output" / EXPERIMENT_NAME

print(f"项目根目录: {PROJECT_ROOT}")
print(f"数据文件: {DATA_FILE}")
print(f"输出目录: {OUTPUT_DIR}")


# ==========================================================

# ================= 修复后的 Dataset (带 Masking) =================
class AssemblyDataset(Dataset):
    def __init__(self, data_file, image_root, processor):
        with open(data_file, "r", encoding="utf-8") as f:
            self.data = json.load(f)
        self.image_root = Path(image_root)
        self.processor = processor

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        item = self.data[idx]

        # 1. 图片加载
        image_list = item["image"]
        if isinstance(image_list, str): image_list = [image_list]
        images = [Image.open(self.image_root / p).convert("RGB") for p in image_list]

        # 2. 对话处理
        conversations = item["conversations"] if "conversations" in item else item["messages"]

        # 3. 生成 Prompt 文本
        text = self.processor.apply_chat_template(
            conversations, tokenize=False, add_generation_prompt=True
        )

        # 4. 转换为 Tensor (inputs 包含 input_ids, attention_mask 等)
        inputs = self.processor(
            text=[text],
            images=images,
            padding=False,
            return_tensors="pt",
        )

        input_ids = inputs["input_ids"].squeeze(0)
        attention_mask = inputs["attention_mask"].squeeze(0)

        # =================== 核心修复：创建 Labels Mask ===================
        # 1. 初始化 Labels 全为 -100 (默认都不算 Loss)
        labels = torch.full_like(input_ids, -100)

        # 2. 找到 Assistant 回复的内容
        # 假设 conversations 最后一个是 assistant 的回复
        last_msg = conversations[-1]
        if last_msg["role"] == "assistant":
            assistant_content = last_msg["content"]

            # 3. 单独 Tokenize 回复内容，计算它的长度
            # add_special_tokens=False 防止加额外的 start/end token 干扰长度计算
            reply_tokens = self.processor.tokenizer(assistant_content, add_special_tokens=False)["input_ids"]
            reply_len = len(reply_tokens)

            # 4. 在 input_ids 的末尾找到这部分内容并解除 Mask
            # 逻辑：input_ids 的最后 reply_len 个 token (可能还有 EOS) 是我们要学的
            # 为了保险，我们取 input_ids 长度和 reply_len 的差值作为切分点

            # 注意：实际 input_ids 可能末尾带 <|im_end|> 或 <|endoftext|>，长度会比 reply_len 多 1-2 个
            # 我们这里采取一个宽松策略：保留最后 (reply_len + 2) 个 token
            valid_len = reply_len + 2

            if len(input_ids) > valid_len:
                # 只把最后 valid_len 个 token 的 label 设为 input_ids 的值
                labels[-valid_len:] = input_ids[-valid_len:]
            else:
                # 极端情况（句子极短），全量学习，防止报错
                labels = input_ids.clone()

        # ================================================================

        return {
            "input_ids": input_ids,
            "attention_mask": attention_mask,
            "labels": labels,  # 现在的 Labels 只有 JSON 部分是有效值
            "pixel_values": inputs["pixel_values"],
            "image_grid_thw": inputs["image_grid_thw"]
        }


# ================= 修复后的 Collator =================
@dataclass
class RobustQwenCollator:
    processor: Any

    def __call__(self, features: List[Dict[str, Any]]) -> Dict[str, Any]:
        max_len = max(f["input_ids"].shape[0] for f in features)

        input_ids_list = []
        attention_mask_list = []
        labels_list = []  # <--- 重点
        pixel_values_list = []
        image_grid_thw_list = []

        for f in features:
            seq_len = f["input_ids"].shape[0]
            pad_len = max_len - seq_len

            # Qwen 的 pad token
            pad_id = self.processor.tokenizer.pad_token_id
            if pad_id is None: pad_id = self.processor.tokenizer.eos_token_id

            # 1. Input IDs Padding
            padded_input_ids = torch.cat([
                f["input_ids"],
                torch.full((pad_len,), pad_id, dtype=torch.long)
            ])
            input_ids_list.append(padded_input_ids)

            # 2. Attention Mask Padding
            padded_att_mask = torch.cat([
                f["attention_mask"],
                torch.zeros((pad_len,), dtype=torch.long)
            ])
            attention_mask_list.append(padded_att_mask)

            # 3. Labels Padding (关键修改！)
            # 不要用 input_ids 填充！要用 f["labels"] (我们在 Dataset 里算好的)
            # Padding 部分填 -100
            padded_labels = torch.cat([
                f["labels"],  # <--- 使用 Dataset 里带 Mask 的 labels
                torch.full((pad_len,), -100, dtype=torch.long)
            ])
            labels_list.append(padded_labels)

            pixel_values_list.append(f["pixel_values"])
            image_grid_thw_list.append(f["image_grid_thw"])

        return {
            "input_ids": torch.stack(input_ids_list),
            "attention_mask": torch.stack(attention_mask_list),
            "labels": torch.stack(labels_list),  # <--- 传入正确的 Labels
            "pixel_values": torch.cat(pixel_values_list, dim=0),
            "image_grid_thw": torch.cat(image_grid_thw_list, dim=0)
        }


def train():
    print("正在初始化 Processor 和 模型...")
    processor = AutoProcessor.from_pretrained(MODEL_ID, trust_remote_code=True)

    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
    )

    model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
        MODEL_ID,
        quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=True
    )
    model.gradient_checkpointing_enable()
    model = prepare_model_for_kbit_training(model)

    peft_config = LoraConfig(
        task_type=TaskType.CAUSAL_LM,
        r=16,
        lora_alpha=32,
        lora_dropout=0.05,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        bias="none",
    )
    model = get_peft_model(model, peft_config)
    model.print_trainable_parameters()

    print(f"Loading Dataset from {DATA_FILE}...")

    print(f"Loading Dataset from {DATA_FILE}...")
    # 直接把所有数据都给 train_dataset，不浪费那 10% 了
    train_dataset = AssemblyDataset(DATA_FILE, IMAGE_ROOT, processor)
    print(f"Dataset loaded. Total samples: {len(train_dataset)}")

    training_args = TrainingArguments(
        output_dir=str(OUTPUT_DIR),  # 转为 string
        per_device_train_batch_size=1,
        gradient_accumulation_steps=16,
        num_train_epochs=4,
        learning_rate=1e-4,
        # === 【修改开始】 ===
        logging_steps=5,
        # === 【核心修改：关闭评估，保命要紧】 ===
        eval_strategy="no",  # 彻底关闭评估，不做任何计算
        # eval_steps=20,              # 注释掉，没用了

        save_strategy="steps",  # 保持按步数保存
        save_steps=20,  # 每 20 步存一个档 (这样你随时 Ctrl+C 都有存档)

        load_best_model_at_end=False,  # 关掉！因为没有评估指标了，没法自动找"最好"
        # metric_for_best_model="eval_loss", # 注释掉
        # greater_is_better=False,    # 注释掉
        # ========================================
        bf16=True,
        fp16=False,
        remove_unused_columns=False,
        report_to="tensorboard",
        logging_dir=str(OUTPUT_DIR / "runs"),
        dataloader_num_workers=0,
        dataloader_pin_memory=False,
        ddp_find_unused_parameters=False,
        # 优化 checkpoint 管理
        save_total_limit=2,  # 只保留最近的2个 checkpoint，节省硬盘
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        # eval_dataset=eval_dataset,     # <--- 删掉或注释掉这一行
        data_collator=RobustQwenCollator(processor=processor),
        # callbacks=[EarlyStoppingCallback(...)] # <--- 删掉或注释掉这一行
    )

    print("开始训练...")
    try:
        # 正常开始训练
        trainer.train()

    except KeyboardInterrupt:
        # 捕获 Ctrl+C 信号
        print("\n\n" + "=" * 30)
        print("⚠️ 检测到用户强制中断 (Ctrl+C)！")
        print("🛑 正在紧急停止训练，并保存当前模型权重...")
        print("=" * 30 + "\n")

    finally:
        # 无论是正常跑完，还是被 Ctrl+C 中断，都会执行这里的保存逻辑
        # 1. 保存最终模型 (LoRA 权重)
        trainer.save_model(str(OUTPUT_DIR))
        # 2. 保存 Processor (确保推理时配置一致)
        processor.save_pretrained(str(OUTPUT_DIR))

        print(f"✅ 模型权重与配置已安全保存至: {OUTPUT_DIR}")


if __name__ == "__main__":
    train()
