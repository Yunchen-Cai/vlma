import os
import json
import torch
import random
import pandas as pd
from pathlib import Path
from tqdm import tqdm
from PIL import Image
from transformers import Qwen2_5_VLForConditionalGeneration, AutoProcessor, BitsAndBytesConfig
from peft import PeftModel

# ================= 配置区域 =================
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
OUTPUT_DIR = PROJECT_ROOT / "output" / "generaltraining_guidedprompt_verification_exp_few_shot"

BASE_MODEL_PATH = PROJECT_ROOT / "cache" / "huggingface" / "hub" / "Qwen2.5-VL-7B-Instruct"
# 🌟 这里的 LORA_PATH 请确保指向你最新微调出来的权重目录
LORA_PATH = PROJECT_ROOT / "output" / "v3.14_few_shot_verification"


DATA_FILES = [
    PROJECT_ROOT / "data" / "3.16test_guided_verification_data.json"
]

IMAGE_ROOT = PROJECT_ROOT / "data"

# ================= 专家级状态核查指导字典 (已更新为 verification: finish/unfinish) =================
GUIDANCE_MAP = {
    "gear housing": " ",

    "drive gear": " ",

    "thrust block": " ",

    "port end cover": " "
}


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
            generated_ids = model.generate(**inputs, max_new_tokens=256)
        generated_ids_trimmed = [out_ids[len(in_ids):] for in_ids, out_ids in zip(inputs.input_ids, generated_ids)]
        output_text = \
        processor.batch_decode(generated_ids_trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False)[0]
        return output_text.strip()
    except Exception as e:
        print(f"Error running VLM: {e}")
        return ""


def extract_json(text):
    try:
        start, end = text.find('{'), text.rfind('}')
        if start != -1 and end != -1: return json.loads(text[start:end + 1])
    except:
        pass
    return {}


# ================= 主实验逻辑 =================
def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 1. 解析数据集
    all_data = []
    for f in DATA_FILES:
        if f.exists():
            all_data.extend(json.load(open(f)))
        else:
            print(f"Warning: Data file not found -> {f}")

    test_samples = []
    for item in all_data:
        try:
            gt_text = item['messages'][1]['content']
            # 🌟 改用脚本自带的 extract_json 提取器，忽略前面的 OBSERVATION 文本
            gt = extract_json(gt_text)

            if not gt:  # 如果提取不到有效 JSON，跳过
                continue

            gt_part = gt.get('part', '').strip()

            # 🌟 动态数据映射逻辑：兼容老数据(status)和新数据(verification)
            if 'verification' in gt:
                gt_verification = gt.get('verification', '').strip().capitalize()  # Finish / Unfinish
            elif 'status' in gt:
                old_status = gt.get('status', '').strip().capitalize()
                gt_verification = "Finish" if old_status == "Correct" else "Unfinish"
            else:
                continue

            if gt_part.lower() in GUIDANCE_MAP:
                img_path = IMAGE_ROOT / item['image'][0]
                if not img_path.exists():
                    img_path = PROJECT_ROOT / item['image'][0]
                if img_path.exists():
                    test_samples.append({
                        "image_path": str(img_path),
                        "gt_part": gt_part,
                        "gt_verification": gt_verification,
                        "guidance": GUIDANCE_MAP[gt_part.lower()]
                    })
        except Exception as e:
            continue

    if not test_samples:
        print("未找到有效测试数据，请检查数据集路径和内容。")
        return

    print(f">>> 找到 {len(test_samples)} 个匹配的测试样本。正在加载模型...")
    model, processor = load_model()
    results = []

    print(">>> 开始 A/B 对比状态核查实验 (Testing Verification)...")

    for s in tqdm(test_samples):
        # -------------------------------------------------------------
        # 🟢 A组：Baseline Prompt (无引导，纯看图判断 finish/unfinish)
        # -------------------------------------------------------------
        prompt_a = (
            f"You are an assembly quality inspector. Observe this frame. "
            f"The worker is handling a {s['gt_part']}. "
            f"Judge whether the action is completed by checking for misalignments, tilting, or incorrect seating.\n\n"
            f"Output ONLY in this JSON format: {{\"action\": \"...\", \"tool\": \"...\", \"part\": \"...\", \"verification\": \"finish/unfinish\"}}."
        )
        res_a_raw = run_vlm(model, processor, s['image_path'], prompt_a)
        # 提取 verification
        res_a = extract_json(res_a_raw).get('verification', 'Unknown').capitalize()
        acc_a = (res_a == s['gt_verification'])

        # -------------------------------------------------------------
        # 🔵 B组：Guided Prompt (植入专家逻辑，基于选项)
        # -------------------------------------------------------------
        prompt_b = (
            f"You are an assembly quality inspector evaluating the {s['gt_part']}.\n\n"
            f"{s['guidance']}"  # 专家字典已经包含了完整的输出格式要求
        )
        res_b_raw = run_vlm(model, processor, s['image_path'], prompt_b)
        res_b_json = extract_json(res_b_raw)
        res_b = res_b_json.get('verification', 'Unknown').capitalize()
        acc_b = (res_b == s['gt_verification'])

        results.append({
            "Image": Path(s['image_path']).name,
            "Part": s['gt_part'],
            "GT_Verification": s['gt_verification'],
            "Pred_A_Baseline": res_a,
            "Acc_A": acc_a,
            "Pred_B_Guided": res_b,
            "Acc_B": acc_b,
            "VLM_Reasoning_B": res_b_raw.replace('\n', ' | ')
        })

    # --- 统计与保存 ---
    df = pd.DataFrame(results)
    raw_path = OUTPUT_DIR / "verification_raw.csv"
    df.to_csv(raw_path, index=False)

    print("\n" + "=" * 60)
    print("📊 动作完成度检验结果 (Action Verification via Guided VLM)")
    print("=" * 60)

    acc_baseline = df['Acc_A'].mean() * 100
    acc_guided = df['Acc_B'].mean() * 100

    print(f"[总体动作验证准确率 Overall Verification Accuracy]")
    print(f"  🟢 Baseline (无引导): {acc_baseline:.2f}%\n  🔵 Guided   (专家引导): {acc_guided:.2f}%")
    print(f"  => Gain: +{acc_guided - acc_baseline:.2f}%\n")

    print("[按零件类型与状态细分 (Breakdown by Part & Verification)]")
    summary = df.groupby(['Part', 'GT_Verification']).agg(
        Samples=('GT_Verification', 'count'),
        Acc_A=('Acc_A', 'mean'),
        Acc_B=('Acc_B', 'mean')
    ).reset_index()
    summary['Acc_A'] = (summary['Acc_A'] * 100).round(2)
    summary['Acc_B'] = (summary['Acc_B'] * 100).round(2)
    summary['Gain'] = summary['Acc_B'] - summary['Acc_A']

    print(summary.to_string(index=False))
    summary.to_csv(OUTPUT_DIR / "verification_summary.csv", index=False)

    print(f"\n✅ 详细实验数据及模型推理记录已保存至: {OUTPUT_DIR}/verification_raw.csv")


if __name__ == "__main__":
    main()