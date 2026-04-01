import os
import json
import torch
import random
import pandas as pd
import numpy as np
from pathlib import Path
from tqdm import tqdm
from PIL import Image
from transformers import Qwen2_5_VLForConditionalGeneration, AutoProcessor, BitsAndBytesConfig
from peft import PeftModel

# ================= 配置区域 =================
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent

BASE_MODEL_PATH = PROJECT_ROOT / "cache" / "huggingface" / "hub" / "Qwen2.5-VL-7B-Instruct"
LORA_PATH = PROJECT_ROOT / "output" / "v1.23_new_simple"

DATA_FILES = [
    PROJECT_ROOT / "data" / "clean_assembly_sft_12.23merged.json",
    PROJECT_ROOT / "data" / "1.27tool_variation_test.json"
]
IMAGE_ROOT = PROJECT_ROOT / "data"

# 实验设置
NUM_ROUNDS = 5  # 跑 5 轮
SAMPLE_SIZE_PER_ROUND = 200  # 每轮随机抽 200 张 (总共 1000 个样本)

# 约束 Prompt (保持与训练一致)
EXTENDED_ALLOWED_TOOLS = ["Hands", "Hex Wrench", "Screwdriver", "Open End Wrench", "Adjustable Wrench", "Hammer"]
ALLOWED_PARTS = ["Mounting Flange", "Gear Housing", "Thrust Block", "Drive Gear", "Driven Gear", "Port End Cover",
                 "Capscrew"]
ALLOWED_ACTIONS = ["Install", "Tighten", "Place", "Insert"]

TOOLS_PROMPT_STR = ", ".join(EXTENDED_ALLOWED_TOOLS)
PARTS_PROMPT_STR = ", ".join(ALLOWED_PARTS)
ACTIONS_PROMPT_STR = ", ".join(ALLOWED_ACTIONS)


# ================= 模型加载 =================
def load_model():
    print(f">>> Loading Model form {BASE_MODEL_PATH}...")
    bnb_config = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4", bnb_4bit_compute_dtype=torch.bfloat16)
    model = Qwen2_5_VLForConditionalGeneration.from_pretrained(str(BASE_MODEL_PATH), device_map="auto",
                                                               quantization_config=bnb_config)
    if LORA_PATH and os.path.exists(LORA_PATH):
        print(f">>> Loading LoRA from {LORA_PATH}...")
        model = PeftModel.from_pretrained(model, str(LORA_PATH))
    processor = AutoProcessor.from_pretrained(str(BASE_MODEL_PATH))
    return model, processor


# ================= 推理核心 =================
def run_vlm(model, processor, image_path, prompt):
    try:
        image = Image.open(image_path).convert("RGB").resize((448, 448))
        messages = [{"role": "user", "content": [{"type": "image", "image": image}, {"type": "text", "text": prompt}]}]
        text_input = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = processor(text=[text_input], images=[image], padding=True, return_tensors="pt").to("cuda")
        with torch.no_grad():
            generated_ids = model.generate(**inputs, max_new_tokens=128)
        generated_ids_trimmed = [out_ids[len(in_ids):] for in_ids, out_ids in zip(inputs.input_ids, generated_ids)]
        output_text = \
        processor.batch_decode(generated_ids_trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False)[0]
        try:
            start, end = output_text.find('{'), output_text.rfind('}')
            if start != -1 and end != -1: return json.loads(output_text[start:end + 1])
        except:
            pass
        return {}
    except:
        return {}


# ================= 混淆矩阵生成工具 =================
def compute_confusion_matrix(df, gt_col, pred_col):
    # 获取所有出现的标签
    labels = sorted(list(set(df[gt_col].unique()) | set(df[pred_col].unique())))
    cm = pd.crosstab(df[gt_col], df[pred_col], rownames=['Actual'], colnames=['Predicted'])
    cm = cm.reindex(index=labels, columns=labels, fill_value=0)
    return cm


# ================= 单轮运行逻辑 =================
def run_single_round(round_idx, model, processor, all_data):
    # 随机采样
    random.shuffle(all_data)
    samples = all_data[:SAMPLE_SIZE_PER_ROUND]

    results = []

    base_prompt = (
        f"You are an assembly quality inspector. Observe this frame. "
        f"Identify the hand action, tool, part, and phase.\n\n"
        f"Constraint 1 - Tools: The tool must be chosen from: [{TOOLS_PROMPT_STR}].\n"
        f"Constraint 2 - Actions: The action must be chosen from: [{ACTIONS_PROMPT_STR}].\n"
        f"Constraint 3 - Parts: The part must be chosen from: [{PARTS_PROMPT_STR}].\n\n"
        f"Output ONLY in this JSON format: "
        f"{{\"action\": \"...\", \"tool\": \"...\", \"part\": \"...\", \"phase\": \"...\"}}."
    )

    print(f"Round {round_idx}: Evaluating {len(samples)} samples...")
    for item in tqdm(samples, leave=False):
        try:
            img_path = IMAGE_ROOT / item['image'][0]
            if not img_path.exists(): img_path = PROJECT_ROOT / item['image'][0]
            if not img_path.exists(): continue

            gt = json.loads(item['messages'][1]['content'])
            gt_tool = gt.get('tool', '').strip().lower()
            gt_part = gt.get('part', '').strip().lower()
            gt_action = gt.get('action', '').strip().lower()

            res = run_vlm(model, processor, str(img_path), base_prompt)

            pred_tool = res.get('tool', 'n/a').strip().lower()
            pred_part = res.get('part', 'n/a').strip().lower()
            pred_action = res.get('action', 'n/a').strip().lower()

            results.append({
                "round": round_idx,
                "gt_tool": gt_tool, "pred_tool": pred_tool, "tool_correct": gt_tool == pred_tool,
                "gt_part": gt_part, "pred_part": pred_part, "part_correct": gt_part == pred_part,
                "gt_action": gt_action, "pred_action": pred_action, "action_correct": gt_action == pred_action
            })
        except:
            continue

    return results


# ================= 主程序 =================
def main():
    # 1. 加载数据
    print(">>> [Step 1] Loading Datasets...")
    all_data = []
    for f_path in DATA_FILES:
        if f_path.exists():
            data = json.load(open(f_path))
            print(f"  - Loaded {len(data)} samples from {f_path.name}")
            all_data.extend(data)
    if not all_data: return

    model, processor = load_model()

    # 2. 循环实验
    all_results = []
    print(f">>> [Step 2] Starting {NUM_ROUNDS} Rounds of Baseline Evaluation...")
    for r in range(1, NUM_ROUNDS + 1):
        round_res = run_single_round(r, model, processor, all_data)
        all_results.extend(round_res)

    df = pd.DataFrame(all_results)
    df.to_csv(PROJECT_ROOT / "src" / "baseline_repeated_raw.csv", index=False)

    # 3. 统计分析
    print("\n" + "=" * 60)
    print(f"📊 Baseline Evaluation Report ({NUM_ROUNDS} Rounds, N={len(df)})")
    print("=" * 60)

    # --- 总体统计 ---
    print(f"[Overall Mean Accuracy]")
    print(f"  Tool Accuracy:   {df['tool_correct'].mean() * 100:.2f}%")
    print(f"  Part Accuracy:   {df['part_correct'].mean() * 100:.2f}%")
    print(f"  Action Accuracy: {df['action_correct'].mean() * 100:.2f}%")
    print("-" * 60)

    # --- 细分统计 (Per-Category Breakdown) ---
    def generate_summary(col_gt, col_correct, fname):
        # 按类别分组，计算平均准确率和样本数
        summary = df.groupby(col_gt)[col_correct].agg(['count', 'mean']).reset_index()
        summary['mean'] *= 100
        summary.columns = ['Category', 'Total Samples', 'Accuracy (%)']
        summary = summary.sort_values('Accuracy (%)', ascending=True)  # 弱项排前面

        # 打印 Top 5 弱项
        print(f">>> Weakest {fname}:")
        print(summary.head(5).to_string(index=False))
        print("")

        summary.to_csv(PROJECT_ROOT / "src" / f"baseline_summary_{fname.lower()}.csv", index=False)
        return summary

    print(f"[Category Breakdown]")
    generate_summary('gt_tool', 'tool_correct', 'Tools')
    generate_summary('gt_part', 'part_correct', 'Parts')
    generate_summary('gt_action', 'action_correct', 'Actions')
    print("-" * 60)

    # --- 混淆矩阵 ---
    print(f"[Generating Aggregate Confusion Matrices]")
    tool_cm = compute_confusion_matrix(df, 'gt_tool', 'pred_tool')
    part_cm = compute_confusion_matrix(df, 'gt_part', 'pred_part')
    action_cm = compute_confusion_matrix(df, 'gt_action', 'pred_action')

    tool_cm.to_csv(PROJECT_ROOT / "src" / "baseline_cm_tools.csv")
    part_cm.to_csv(PROJECT_ROOT / "src" / "baseline_cm_parts.csv")
    action_cm.to_csv(PROJECT_ROOT / "src" / "baseline_cm_actions.csv")

    print("Files Saved:")
    print("  - baseline_repeated_raw.csv (Raw Data)")
    print("  - baseline_summary_*.csv (Accuracy Tables)")
    print("  - baseline_cm_*.csv (Confusion Matrices)")
    print("=" * 60)


if __name__ == "__main__":
    main()