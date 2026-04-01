import os
import json
import torch
import random
import pandas as pd
import numpy as np
import cv2
from pathlib import Path
from tqdm import tqdm
from PIL import Image
import matplotlib.pyplot as plt
from transformers import Qwen2_5_VLForConditionalGeneration, AutoProcessor, BitsAndBytesConfig
from peft import PeftModel

# ================= 配置区域 =================
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent

# 请确保路径与您的 image_01511c.png 结构一致
BASE_MODEL_PATH = PROJECT_ROOT / "cache" / "huggingface" / "hub" / "Qwen2.5-VL-7B-Instruct"
LORA_PATH = PROJECT_ROOT / "output" / "v1.23_new_simple"

DATA_FILES = [
    PROJECT_ROOT / "data" / "clean_assembly_sft_12.23merged.json",
    PROJECT_ROOT / "data" / "1.27tool_variation_test.json"
]
IMAGE_ROOT = PROJECT_ROOT / "data"
SAVE_VIZ_DIR = PROJECT_ROOT / "visualizations" / "attention_results"
SAVE_VIZ_DIR.mkdir(parents=True, exist_ok=True)

SAMPLE_SIZE = 10  # 实验一轮，抽取10个典型样本进行可视化分析

# 基础约束
EXTENDED_ALLOWED_TOOLS = ["Hands", "Hex Wrench", "Screwdriver", "Open End Wrench", "Adjustable Wrench", "Hammer"]
ALLOWED_PARTS = ["Mounting Flange", "Gear Housing", "Thrust Block", "Drive Gear", "Driven Gear", "Port End Cover",
                 "Capscrew"]
ALLOWED_ACTIONS = ["Install", "Tighten", "Place", "Insert"]

TOOLS_PROMPT_STR = ", ".join(EXTENDED_ALLOWED_TOOLS)
PARTS_PROMPT_STR = ", ".join(ALLOWED_PARTS)
ACTIONS_PROMPT_STR = ", ".join(ALLOWED_ACTIONS)

# 特征驱动的 Guided Map (用于实验组 C)
GUIDANCE_MAP = {
    "tools": {
        "adjustable wrench": "CRITICAL: Look for a thick handle and a thumbwheel (worm screw) near the jaw. DO NOT CONFUSE with Hex Wrench (which is a thin metal bar).",
        "hex wrench": "A simple L-shaped or T-shaped metal bar. Distinct from Screwdrivers (which have distinct handles).",
        "screwdriver": "Look for a dedicated handle and a long shaft ending in a tip. DO NOT CONFUSE with Hex Wrench.",
        "open end wrench": "Look for a C-shaped or U-shaped opening at the end. Distinct from L-shaped Hex Wrenches.",
        "hammer": "Look for a heavy head perpendicular to the handle.",
        "hands": "Human fingers interacting directly with the assembly."
    },
    "parts": {
        "drive gear": "A large circular gear with teeth. Distinguish from small threaded bolts (Capscrews).",
        "driven gear": "The secondary circular gear with teeth.",
        "thrust block": "A solid block component. Distinguish from flat Cover Plates or Gears (it has no teeth).",
        "gear housing": "The large outer metallic casing. Distinguish from smaller solid blocks.",
        "capscrew": "Small threaded bolts with heads. Distinguish from larger Gears.",
        "mounting flange": "Flat plate with holes.",
        "port end cover": "Cover plate."
    },
    "actions": {
        "install": "General assembly action involving securing parts. Distinguish from simple Placement.",
        "place": "Positioning a part onto a surface. Distinguish from Insert (putting into a hole).",
        "insert": "Putting a part INTO a hole. Distinct from Place.",
        "tighten": "Using a tool to rotate a fastener."
    }
}


# ================= 模型加载 =================
def load_model():
    print(f">>> Loading Model from {BASE_MODEL_PATH}...")
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True, bnb_4bit_quant_type="nf4", bnb_4bit_compute_dtype=torch.bfloat16
    )
    model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
        str(BASE_MODEL_PATH),
        device_map="auto",
        quantization_config=bnb_config,
        output_attentions=True  # 必须开启
    )
    if LORA_PATH.exists():
        print(f">>> Loading LoRA from {LORA_PATH}...")
        model = PeftModel.from_pretrained(model, str(LORA_PATH))
    processor = AutoProcessor.from_pretrained(str(BASE_MODEL_PATH))
    return model, processor


# ================= 注意力提取与推理 =================
def run_vlm_with_attention(model, processor, image_path, prompt, target_keyword="tool"):
    try:
        image = Image.open(image_path).convert("RGB")
        messages = [{"role": "user", "content": [{"type": "image", "image": image}, {"type": "text", "text": prompt}]}]
        text_input = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = processor(text=[text_input], images=[image], return_tensors="pt").to("cuda")

        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=64,  # 缩短生成长度，减少崩坏概率
                do_sample=False,
                output_attentions=True,
                return_dict_in_generate=True,
                repetition_penalty=1.2  # 强制打破乱码循环
            )

        # 1. 提取生成的 Token 并寻找关键词索引
        generated_ids = outputs.sequences[0][len(inputs.input_ids[0]):]
        tokens = [processor.decode([tid]).lower().strip() for tid in generated_ids]
        full_text = processor.batch_decode([generated_ids], skip_special_tokens=True)[0]

        # 寻找包含目标词（如 'wrench'）的索引，若无则取 JSON 的 key 附近位置
        target_idx = next((i for i, t in enumerate(tokens) if target_keyword in t), 5)

        # 2. 提取 Cross-Attention (热力图逻辑)
        if hasattr(outputs, 'cross_attentions') and len(outputs.cross_attentions) > target_idx:
            attn_matrix = outputs.cross_attentions[target_idx][-1]  # 取目标 token 的最后一层注意力
            avg_attn = attn_matrix.mean(dim=1).detach().cpu()
            avg_attn = torch.nan_to_num(avg_attn, nan=0.0)  # 排除 NaN 干扰

            # 取出 token 对图像的 1D 注意力权重
            token_attn = avg_attn[0, -1, :]

            # 动态映射回 2D 网格 (Qwen2.5-VL 28x28 patch)
            grid_size = int(np.sqrt(token_attn.shape[0]))
            heatmap = token_attn.reshape(grid_size, grid_size).numpy()

            # 平滑处理：让热力图看起来像“焦点”而非“方块”
            heatmap = cv2.GaussianBlur(heatmap, (3, 3), 0)
            heatmap = cv2.resize(heatmap, (image.size[0], image.size[1]))

            # 过滤背景背景噪声，只保留高权重区域
            heatmap = (heatmap - heatmap.min()) / (heatmap.max() - heatmap.min() + 1e-12)
        else:
            heatmap = np.zeros((image.size[1], image.size[0]))

        return full_text, heatmap

    except Exception as e:
        return f"ERROR: {e}", np.zeros((448, 448))


# ================= 实验主程序 =================
def main():
    all_data = []
    for f in DATA_FILES:
        if f.exists(): all_data.extend(json.load(open(f)))

    random.shuffle(all_data)
    model, processor = load_model()

    results = []
    print(f">>> 开始 A/C 对照实验与注意力可视化 (样本数: {SAMPLE_SIZE})...")

    for i in tqdm(range(SAMPLE_SIZE)):
        item = all_data[i]
        img_path = IMAGE_ROOT / item['image'][0]
        if not img_path.exists(): continue

        gt = json.loads(item['messages'][1]['content'])
        gt_tool = gt.get('tool', '').lower().strip()
        gt_part = gt.get('part', '').lower().strip()

        # 构造 Prompts
        constraints = f"Constraint: Tools[{TOOLS_PROMPT_STR}], Parts[{PARTS_PROMPT_STR}]. Output JSON."

        p_a = f"You are an assembly inspector. Identify the tool and part in this frame.\n{constraints}"

        guide_t = GUIDANCE_MAP['tools'].get(gt_tool, "standard tool")
        guide_p = GUIDANCE_MAP['parts'].get(gt_part, "standard part")
        p_c = (f"You are an assembly inspector. VISUAL FOCUS GUIDANCE: "
               f"Look for {guide_t} and {guide_p}. Specifically check the interaction point.\n{constraints}")

        # 获取结果与热力图
        text_a, map_a = run_vlm_with_attention(model, processor, img_path, p_a)
        text_b, map_c = run_vlm_with_attention(model, processor, img_path, p_c)

        # 保存可视化对比图
        fig, axes = plt.subplots(1, 2, figsize=(16, 8))
        raw_img = plt.imread(img_path)

        # 绘图 A
        axes[0].imshow(raw_img)
        axes[0].imshow(map_a, cmap='jet', alpha=0.4)
        axes[0].set_title(f"Baseline (Group A)\nOutput: {text_a[:40]}...")
        axes[0].axis('off')

        # 绘图 C
        axes[1].imshow(raw_img)
        axes[1].imshow(map_c, cmap='jet', alpha=0.4)
        axes[1].set_title(f"Guided (Group C)\nOutput: {text_b[:40]}...")
        axes[1].axis('off')

        plt.tight_layout()
        plt.savefig(SAVE_VIZ_DIR / f"attention_compare_{i}_{gt_tool}.png")
        plt.close()

        results.append({
            "Sample": i, "GT_Tool": gt_tool,
            "Acc_A": gt_tool in text_a.lower(),
            "Acc_C": gt_tool in text_b.lower()
        })

    # 输出统计
    df = pd.DataFrame(results)
    print("\n" + "=" * 50)
    print(f"实验完成！\nBaseline Accuracy: {df['Acc_A'].mean() * 100:.2f}%")
    print(f"Guided Accuracy: {df['Acc_C'].mean() * 100:.2f}%")
    print(f"可视化结果已保存至: {SAVE_VIZ_DIR}")
    print("=" * 50)


if __name__ == "__main__":
    main()