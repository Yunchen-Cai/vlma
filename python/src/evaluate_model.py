import os
import json
import torch
import pandas as pd
from tqdm import tqdm
from pathlib import Path

# === 关键修改：在这里加上 BitsAndBytesConfig ===
from transformers import (
    Qwen2_5_VLForConditionalGeneration,
    AutoProcessor,
    BitsAndBytesConfig  # <--- 必须加上这个！
)
# ============================================

from qwen_vl_utils import process_vision_info
from peft import PeftModel


EXTENDED_ALLOWED_TOOLS = [
    "Hands",
    "Hex Wrench",
    "Screwdriver",      # 新增
    "Open End Wrench",  # 新增
    "adjustable wrench",# 新增
    "Hammer"            # 新增
]

# 这一段是你指出的关键补充：
ALLOWED_PARTS = [
    "Mounting Flange",
    "Gear Housing",
    "Thrust Block",
    "Drive Gear",
    "Driven Gear",
    "Port End Cover",
    "Capscrew"
]
ALLOWED_ACTIONS = [
    "Install",
    "Tighten",
    "Place",
    "Insert"
]

# 转为字符串
TOOLS_PROMPT_STR = ", ".join(EXTENDED_ALLOWED_TOOLS)
PARTS_PROMPT_STR = ", ".join(ALLOWED_PARTS) # 新增
ACTIONS_PROMPT_STR = ", ".join(ALLOWED_ACTIONS) # 新增这一行
# ================= 动态路径配置 (复制自您的训练代码) =================
# 1. 获取项目根目录
# 假设脚本在 D:\vlm_assembly\src\evaluate_model.py
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent

print(f"项目根目录锁定为: {PROJECT_ROOT}")

# 2. 关键路径配置
# 测试集文件 (自动拼接绝对路径)
TEST_DATA_PATH = PROJECT_ROOT / "data" / "1.27tool_variation_test.json"

# 模型路径 (建议用绝对路径，或者指向 cache)
BASE_MODEL_PATH = r"D:\vlm_assembly\cache\huggingface\hub\Qwen2.5-VL-7B-Instruct"

# LoRA 路径 (Few-shot 实验用)
# 如果是 Zero-shot，请注释掉下面这行或设为 None
LORA_PATH = PROJECT_ROOT / "output" / "v1.23_new_simple"
# LORA_PATH = None  # Zero-shot 时用这行

# 结果保存路径
OUTPUT_CSV = PROJECT_ROOT / "output" / "evaluation_tools_fewshot.csv"
# OUTPUT_CSV = PROJECT_ROOT / "output" / "evaluation_tools_zeroshot.csv" # <-- 改名，防止覆盖
# 图片根目录 (非常重要！)
# 如果你的图片都在 data 文件夹里 (比如 data/temp_frames_12.23merged/...)，就保留下面这行
# 如果你的图片在项目根目录下 (比如 D:\vlm_assembly\temp_frames_12.23merged/...)，请改为: IMAGE_ROOT = PROJECT_ROOT
IMAGE_ROOT = PROJECT_ROOT / "data"
# ================================================================
def load_model(base_path, lora_path=None):
    print(f"正在加载基座模型 (4-bit 量化): {base_path}...")

    # 1. 定义 4-bit 量化配置 (关键修改)
    quantization_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
        bnb_4bit_quant_type="nf4"
    )

    # 2. 加载模型时传入 quantization_config
    model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
        base_path,
        quantization_config=quantization_config,  # <--- 启用量化
        device_map="auto",
        torch_dtype=torch.bfloat16,
    )

    if lora_path:
        print(f"正在加载 LoRA 适配器: {lora_path}...")
        model = PeftModel.from_pretrained(model, lora_path)

    processor = AutoProcessor.from_pretrained(base_path)
    return model, processor


def parse_json_output(text):
    """尝试从模型输出中提取 JSON"""
    try:
        # 找到第一个 { 和最后一个 }
        start = text.find('{')
        end = text.rfind('}') + 1
        if start != -1 and end != -1:
            json_str = text[start:end]
            return json.loads(json_str)
    except:
        pass
    return {}


def evaluate():
    # 1. 加载数据
    with open(TEST_DATA_PATH, 'r') as f:
        data = json.load(f)

    print(f"测试集大小: {len(data)} 样本")

    # 2. 加载模型
    model, processor = load_model(BASE_MODEL_PATH, LORA_PATH)
    model.eval()

    results = []

    # 3. 开始推理循环
    for item in tqdm(data, desc="Evaluating"):
        # =================================================
        # 步骤 A: 提取 Ground Truth (保持不变)
        # =================================================
        try:
            ground_truth_str = item['messages'][1]['content']
            ground_truth = json.loads(ground_truth_str)
        except Exception as e:
            print(f"\n[Warning] 解析 Ground Truth 失败: {e}")
            continue

        # =================================================
        # 步骤 B: 修复图片路径 + 【关键】注入 Zero-shot Prompt
        # =================================================
        raw_user_content = item['messages'][0]['content']
        new_user_content = []
        current_image_path = "Unknown"

        for content_item in raw_user_content:
            # 1. 处理图片 (转绝对路径)
            if content_item['type'] == 'image':
                rel_path = content_item['image']
                abs_path = IMAGE_ROOT / rel_path
                abs_path_str = str(abs_path)
                current_image_path = rel_path

                if not abs_path.exists():
                    print(f"\n[Error] 找不到图片: {abs_path_str}")
                    break

                new_item = content_item.copy()
                new_item['image'] = abs_path_str
                new_user_content.append(new_item)

            # 2. 处理文本 (强行替换为包含新列表的 Prompt)
            elif content_item['type'] == 'text':
                # 这里我们忽略 JSON 里原本的 text，直接用带有新列表的 Prompt 覆盖
                new_prompt = (
                    f"You are an assembly quality inspector. Observe this frame. "
                    f"Identify the hand action, tool, part, and phase.\n\n"
                    
                    f"Constraint 1 - Tools: The tool must be chosen from: [{TOOLS_PROMPT_STR}].\n"
                    f"Constraint 2 - Actions: The action must be chosen from: [{ACTIONS_PROMPT_STR}].\n" # <--- 新增 Action 限制
                    f"Constraint 3 - Parts: The part must be chosen from: [{PARTS_PROMPT_STR}].\n\n"
                    
                    f"Output ONLY in this JSON format: "
                    f"{{\"action\": \"...\", \"tool\": \"...\", \"part\": \"...\", \"phase\": \"...\"}}."
                )

                new_item = content_item.copy()
                new_item['text'] = new_prompt
                new_user_content.append(new_item)

        if len(new_user_content) != len(raw_user_content):
            continue

        # 构建 Messages
        messages = [{"role": "user", "content": new_user_content}]

        # =================================================
        # 步骤 C & D: 推理和对比 (保持不变)
        # =================================================
        # ... (直接保留你原来的代码即可) ...
        # (为了方便，下面我也贴出了后续代码，确保你粘贴时不出错)

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
            output_text = processor.batch_decode(
                generated_ids, skip_special_tokens=True
            )[0]

            if "assistant" in output_text:
                response_text = output_text.split("assistant")[-1].strip()
            else:
                response_text = output_text

            prediction = parse_json_output(response_text)

        # 记录结果
        is_correct_tool = prediction.get('tool', '').lower() == ground_truth.get('tool', '').lower()
        is_correct_action = prediction.get('action', '').lower() == ground_truth.get('action', '').lower()
        is_correct_part = prediction.get('part', '').lower() == ground_truth.get('part', '').lower()

        results.append({
            "image": current_image_path,
            "gt_tool": ground_truth.get('tool'),
            "pred_tool": prediction.get('tool'),
            "tool_correct": is_correct_tool,
            "gt_action": ground_truth.get('action'),
            "pred_action": prediction.get('action'),
            "action_correct": is_correct_action,
            "gt_part": ground_truth.get('part'),
            "pred_part": prediction.get('part'),
            "part_correct": is_correct_part
        })

    # 4. 生成报告
    if len(results) == 0:
        print("没有产生任何结果，请检查数据路径是否正确。")
        return

    df = pd.DataFrame(results)

    tool_acc = df['tool_correct'].mean() * 100
    action_acc = df['action_correct'].mean() * 100
    part_acc = df['part_correct'].mean() * 100

    print("\n" + "=" * 30)
    print(f"EVALUATION REPORT")
    print(f"Model: {'Few-shot (LoRA)' if LORA_PATH else 'Zero-shot (Base)'}")
    print(f"Tool Accuracy:   {tool_acc:.2f}%")
    print(f"Action Accuracy: {action_acc:.2f}%")
    print(f"Part Accuracy:   {part_acc:.2f}%")
    print("=" * 30 + "\n")

    # 确保输出目录存在
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_CSV, index=False)
    print(f"详细结果已保存至: {OUTPUT_CSV}")


if __name__ == "__main__":
    evaluate()