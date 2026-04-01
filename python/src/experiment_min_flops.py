import os
import json
import torch
import pandas as pd
from tqdm import tqdm
from PIL import Image
from pathlib import Path
import matplotlib.pyplot as plt

# === HuggingFace 组件 ===
from transformers import (
    Qwen2_5_VLForConditionalGeneration,
    AutoProcessor,
    BitsAndBytesConfig
)
from qwen_vl_utils import process_vision_info
from peft import PeftModel

# ================= 1. 配置区域 =================
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent

# 路径
TEST_DATA_PATH = PROJECT_ROOT / "data" / "1.26.test.json"
BASE_MODEL_PATH = r"D:\vlm_assembly\cache\huggingface\hub\Qwen2.5-VL-7B-Instruct"
LORA_PATH = PROJECT_ROOT / "output" / "v1.23_new_simple"

OUTPUT_CSV = PROJECT_ROOT / "output" / "resolution_trend_16_9_final.csv"
OUTPUT_PLOT = PROJECT_ROOT / "output" / "resolution_trend_16_9_final_plot.png"
IMAGE_ROOT = PROJECT_ROOT / "data"

# === 关键修改：扩展测试分辨率列表 ===
# 1. 低于 360p 的部分：72p 间隔 -> [144, 216, 288]
low_res = list(range(144, 360, 72))

# 2. 360p 及以上的部分：180p 间隔 -> [360, 540, 720, 900, 1080]
high_res = list(range(360, 1081, 180))

# 合并并排序
HEIGHTS_TO_TEST = sorted(low_res + high_res)
# 最终列表: [144, 216, 288, 360, 540, 720, 900, 1080]

# ================= 2. 标签定义 =================
EXTENDED_ALLOWED_TOOLS = [
    "Hands", "Hex Wrench", "Screwdriver",
    "Open End Wrench", "adjustable wrench", "Hammer"
]
ALLOWED_PARTS = [
    "Mounting Flange", "Gear Housing", "Thrust Block",
    "Drive Gear", "Driven Gear", "Port End Cover", "Capscrew"
]
ALLOWED_ACTIONS = [
    "Install", "Tighten", "Place", "Insert"
]

TOOLS_PROMPT_STR = ", ".join(EXTENDED_ALLOWED_TOOLS)
PARTS_PROMPT_STR = ", ".join(ALLOWED_PARTS)
ACTIONS_PROMPT_STR = ", ".join(ALLOWED_ACTIONS)


# ================= 3. 辅助函数 =================
def resize_by_height(image, target_height):
    """
    将图片缩放到指定高度 target_height，并强制宽度为 16:9 比例。
    """
    # 计算对应的 16:9 宽度
    target_width = int(target_height * 16 / 9)

    # 强制缩放 (原图为16:9，则为等比缩放)
    img_resized = image.resize((target_width, target_height), Image.Resampling.LANCZOS)

    return img_resized


def parse_json_output(text):
    try:
        start = text.find('{')
        end = text.rfind('}') + 1
        if start != -1 and end != -1:
            json_str = text[start:end]
            return json.loads(json_str)
    except:
        pass
    return {}


def load_model(base_path, lora_path=None):
    print(f"正在加载基座模型 (4-bit 量化): {base_path}...")
    quantization_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
        bnb_4bit_quant_type="nf4"
    )
    model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
        base_path,
        quantization_config=quantization_config,
        device_map="auto",
        torch_dtype=torch.bfloat16,
    )
    if lora_path:
        print(f"正在加载 LoRA: {lora_path}...")
        model = PeftModel.from_pretrained(model, lora_path)

    processor = AutoProcessor.from_pretrained(base_path)
    return model, processor


# ================= 4. 评估函数 =================
def evaluate_resolution(model, processor, data, height):
    width = int(height * 16 / 9)
    print(f"\n>>> Running Evaluation for {height}p ({width}x{height})")

    correct_tool = 0
    correct_action = 0
    correct_part = 0
    total = 0

    DETAILED_PROMPT = (
        f"You are an assembly quality inspector. Observe this frame. "
        f"Identify the hand action, tool, part, and phase.\n\n"
        f"Constraint 1 - Tools: The tool must be chosen from: [{TOOLS_PROMPT_STR}].\n"
        f"Constraint 2 - Actions: The action must be chosen from: [{ACTIONS_PROMPT_STR}].\n"
        f"Constraint 3 - Parts: The part must be chosen from: [{PARTS_PROMPT_STR}].\n\n"
        f"Output ONLY in this JSON format: "
        f"{{\"action\": \"...\", \"tool\": \"...\", \"part\": \"...\", \"phase\": \"...\"}}."
    )

    for item in tqdm(data, desc=f"{height}p", leave=False):
        try:
            gt_json = json.loads(item['messages'][1]['content'])
        except:
            continue

        raw_user_content = item['messages'][0]['content']
        image_path = None
        for content in raw_user_content:
            if content['type'] == 'image':
                rel_path = content['image']
                image_path = IMAGE_ROOT / rel_path
                break

        if not image_path or not image_path.exists():
            continue

        try:
            img = Image.open(image_path).convert("RGB")
            img_input = resize_by_height(img, height)
        except Exception as e:
            print(f"Img Error: {e}")
            continue

        messages = [{
            "role": "user",
            "content": [
                {"type": "image", "image": img_input},
                {"type": "text", "text": DETAILED_PROMPT},
            ],
        }]

        text = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        image_inputs, video_inputs = process_vision_info(messages)

        inputs = processor(
            text=[text],
            images=image_inputs,
            padding=True,
            return_tensors="pt",
        ).to("cuda")

        with torch.no_grad():
            generated_ids = model.generate(**inputs, max_new_tokens=128)
            output_text = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]

            if "assistant" in output_text:
                response = output_text.split("assistant")[-1].strip()
            else:
                response = output_text

            pred_json = parse_json_output(response)

        pred_tool = pred_json.get('tool', '').strip().lower()
        gt_tool = gt_json.get('tool', '').strip().lower()
        pred_action = pred_json.get('action', '').strip().lower()
        gt_action = gt_json.get('action', '').strip().lower()
        pred_part = pred_json.get('part', '').strip().lower()
        gt_part = gt_json.get('part', '').strip().lower()

        if pred_tool == gt_tool: correct_tool += 1
        if pred_action == gt_action: correct_action += 1
        if pred_part == gt_part: correct_part += 1
        total += 1

    if total == 0: return 0, 0, 0
    return (correct_tool / total) * 100, (correct_action / total) * 100, (correct_part / total) * 100


# ================= 5. 主程序 =================
def main():
    print(f"Loading data from {TEST_DATA_PATH}...")
    with open(TEST_DATA_PATH, 'r') as f:
        full_data = json.load(f)
    print(f"Total samples: {len(full_data)}")

    model, processor = load_model(BASE_MODEL_PATH, LORA_PATH)
    model.eval()

    results = []

    print(f"Heights to test: {HEIGHTS_TO_TEST}")

    for h in HEIGHTS_TO_TEST:
        acc_tool, acc_action, acc_part = evaluate_resolution(model, processor, full_data, h)

        w = int(h * 16 / 9)
        label_str = f"{w}x{h}"

        print(f"Result for {label_str} -> Tool: {acc_tool:.2f}%, Action: {acc_action:.2f}%, Part: {acc_part:.2f}%")

        results.append({
            "Height": h,
            "Width": w,
            "Resolution_Label": label_str,
            "Tool_Acc": acc_tool,
            "Action_Acc": acc_action,
            "Part_Acc": acc_part
        })

    # 保存 CSV
    df = pd.DataFrame(results)
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_CSV, index=False)
    print(f"\nData saved to {OUTPUT_CSV}")

    # 画图
    plt.figure(figsize=(12, 7))
    plt.plot(df["Height"], df["Tool_Acc"], marker='o', label='Tool Accuracy', linewidth=2)
    plt.plot(df["Height"], df["Action_Acc"], marker='s', label='Action Accuracy', linewidth=2)
    plt.plot(df["Height"], df["Part_Acc"], marker='^', label='Part Accuracy', linewidth=2)

    plt.title(f"Accuracy vs. Image Resolution (16:9 Aspect Ratio)", fontsize=14)
    plt.xlabel("Resolution (Height p)", fontsize=12)
    plt.ylabel("Accuracy (%)", fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend(fontsize=12)
    plt.ylim(0, 105)

    # 设置 X 轴刻度，让它显示所有测试点
    plt.xticks(df["Height"], df["Resolution_Label"], rotation=45)

    plt.tight_layout()
    plt.savefig(OUTPUT_PLOT)
    print(f"Trend plot saved to {OUTPUT_PLOT}")


if __name__ == "__main__":
    main()