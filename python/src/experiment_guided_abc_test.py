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

NUM_ROUNDS = 3
SAMPLE_SIZE_PER_ROUND = 150

# === 1. 数据驱动的基准性能 (基于你之前的 Baseline 报告) ===
# 准确率 < 85% 的将被标记为“弱项”，触发 C 组的强力引导
BASELINE_PERFORMANCE = {
    # Tools
    "hands": 100.0,
    "hex wrench": 60.4,  # ⚠️ Weak
    "adjustable wrench": 58.6,  # 🚨 Critical
    "screwdriver": 50.0,  # 🚨 Critical
    "open end wrench": 0.0,  # 💀 Dead
    "hammer": 80.0,

    # Parts
    "mounting flange": 100.0,
    "port end cover": 97.3,
    "capscrew": 96.7,
    "driven gear": 95.1,
    "gear housing": 81.6,  # ⚠️ Weak
    "drive gear": 79.8,  # ⚠️ Weak
    "thrust block": 48.6,  # 🚨 Critical

    # Actions
    "tighten": 93.5,
    "insert": 93.3,
    "place": 76.5,  # ⚠️ Weak
    "install": 6.9  # 💀 Dead
}

# === 2. 判别性细节指导 (Discriminative Detail Guidance) ===
# 修改核心：不给结论，而是给出“如何区分”的方法论，引导模型关注最具区分度的视觉特征
GUIDANCE_MAP = {
    "tools": {
        "adjustable wrench": "DISTINCTION CHECK: Look specifically at the head. Does it have a **spiral thumb-wheel (worm screw)**? If yes, it is an Adjustable Wrench. Do not confuse with the simple bar shape of a Hex Wrench.",
        "hex wrench": "DISTINCTION CHECK: Look at the handle area. Is it just a **thin metal bar** (L-shaped or straight) WITHOUT a separate grip? If yes, it is a Hex Wrench. Screwdrivers usually have thick plastic handles.",
        "screwdriver": "DISTINCTION CHECK: Look at the grip. Does it have a **distinct thick handle** (often plastic or rubber) that is wider than the shaft? If yes, it is a Screwdriver.",
        "open end wrench": "DISTINCTION CHECK: Look at the tip. Is there a **C-shaped or U-shaped opening** meant to slide onto a bolt from the side? This distinguishes it from ring spanners or socket drivers.",
        "hammer": "DISTINCTION CHECK: Look at the head shape. Is there a **heavy, T-shaped metal block** perpendicular to the handle? Used for striking, not turning.",
        "hands": "DISTINCTION CHECK: Are there **human fingers** directly touching the part? Ensure no tool is being held/used."
    },
    "parts": {
        "drive gear": "DISTINCTION CHECK: Look at the context. Is this the **primary/central gear** that drives others? Contrast with the Driven Gear which meshes with it.",
        "driven gear": "DISTINCTION CHECK: Look at the interaction. Is this gear **being turned** by another gear (the Drive Gear)?",
        "thrust block": "DISTINCTION CHECK: Look for teeth. Is this a **solid block component** with smooth or irregular edges? If it has gear teeth, it is NOT a Thrust Block.",
        "gear housing": "DISTINCTION CHECK: Scale check. Is this the **large outer metallic shell** that contains other parts? It should be much larger than screws or blocks.",
        "capscrew": "DISTINCTION CHECK: Size check. Is this a **small threaded fastener**? Distinguish from larger components like Drive Gears or Flanges.",
        "mounting flange": "DISTINCTION CHECK: Look for shape. Is it a **flat circular plate** with multiple bolt holes along the rim?",
        "port end cover": "DISTINCTION CHECK: Is it a **flat cover plate** attached to the housing?"
    },
    "actions": {
        "install": "DISTINCTION CHECK: Complexity check. Is the part being **secured or fastened** into place? If it's just being laid down loosely, it's 'Place'.",
        "place": "DISTINCTION CHECK: Depth check. Is the part just **resting on the surface**? If it is entering INSIDE a hole, it is 'Insert'. If it is being rotated, it is 'Tighten'.",
        "insert": "DISTINCTION CHECK: Position check. Is the part **entering into a hole** or cavity? Look for partial occlusion of the part as it goes in.",
        "tighten": "DISTINCTION CHECK: Motion check. Is the tool/hand **applying rotational force**? Look for grip posture suggesting turning."
    }
}

# 冲突字典 (用于 B 组制造干扰)
TOOL_CONFLICTS = {
    "hex wrench": "Screwdriver", "screwdriver": "Hex Wrench",
    "adjustable wrench": "Hex Wrench",
    "hands": "Hex Wrench",
    "hammer": "Adjustable Wrench", "open end wrench": "Hex Wrench"
}
PART_CONFLICTS = {
    "drive gear": "Capscrew",
    "driven gear": "Drive Gear",
    "mounting flange": "Gear Housing", "gear housing": "Thrust Block",
    "capscrew": "Port End Cover", "thrust block": "Port End Cover",
    "port end cover": "Capscrew"
}
ACTION_CONFLICTS = {
    "tighten": "Insert",
    "place": "Insert",
    "install": "Place",
    "insert": "Place"
}

# Standard Prompts
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


# ================= 单轮实验 =================
def run_single_round(round_idx, model, processor, all_data):
    random.shuffle(all_data)
    samples = []
    counts = {"tool": 0, "part": 0, "action": 0}

    for item in all_data:
        if len(samples) >= SAMPLE_SIZE_PER_ROUND: break
        try:
            img_path = IMAGE_ROOT / item['image'][0]
            if not img_path.exists(): img_path = PROJECT_ROOT / item['image'][0]
            if not img_path.exists(): continue

            gt = json.loads(item['messages'][1]['content'])
            gt_tool = gt.get('tool', '').strip()
            gt_part = gt.get('part', '').strip()
            gt_action = gt.get('action', '').strip()

            # --- 智能样本筛选 ---
            test_type = "None"
            # 优先测试弱项
            if BASELINE_PERFORMANCE.get(gt_tool.lower(), 100) < 85:
                test_type = "Tool_Mismatch"
            elif BASELINE_PERFORMANCE.get(gt_part.lower(), 100) < 85:
                test_type = "Part_Mismatch"
            elif BASELINE_PERFORMANCE.get(gt_action.lower(), 100) < 85:
                test_type = "Action_Mismatch"
            else:
                # 随机填充
                candidates = []
                if counts["tool"] < SAMPLE_SIZE_PER_ROUND / 3: candidates.append("Tool_Mismatch")
                if counts["part"] < SAMPLE_SIZE_PER_ROUND / 3: candidates.append("Part_Mismatch")
                if counts["action"] < SAMPLE_SIZE_PER_ROUND / 3: candidates.append("Action_Mismatch")
                if candidates: test_type = random.choice(candidates)
            if test_type == "None": continue

            fake_tool, fake_part, fake_action = gt_tool, gt_part, gt_action
            if test_type == "Tool_Mismatch" and gt_tool.lower() in TOOL_CONFLICTS:
                fake_tool = TOOL_CONFLICTS[gt_tool.lower()]
                counts["tool"] += 1
            elif test_type == "Part_Mismatch" and gt_part.lower() in PART_CONFLICTS:
                fake_part = PART_CONFLICTS[gt_part.lower()]
                counts["part"] += 1
            elif test_type == "Action_Mismatch" and gt_action.lower() in ACTION_CONFLICTS:
                fake_action = ACTION_CONFLICTS[gt_action.lower()]
                counts["action"] += 1
            else:
                continue

            # --- C组: 引导决策逻辑 ---
            should_guide = False
            guidance_text = ""
            perf_val = 100.0
            if test_type == "Tool_Mismatch":
                perf_val = BASELINE_PERFORMANCE.get(gt_tool.lower(), 50.0)
            elif test_type == "Part_Mismatch":
                perf_val = BASELINE_PERFORMANCE.get(gt_part.lower(), 50.0)
            elif test_type == "Action_Mismatch":
                perf_val = BASELINE_PERFORMANCE.get(gt_action.lower(), 50.0)

            if perf_val < 85.0:
                should_guide = True
                t_g = GUIDANCE_MAP["tools"].get(gt_tool.lower(), "")
                p_g = GUIDANCE_MAP["parts"].get(gt_part.lower(), "")
                a_g = GUIDANCE_MAP["actions"].get(gt_action.lower(), "")

                # 组装指导文本，只包含相关的部分
                guidance_text = ""
                if test_type == "Tool_Mismatch": guidance_text += f"- Tool Check: {t_g}\n"
                if test_type == "Part_Mismatch": guidance_text += f"- Part Check: {p_g}\n"
                if test_type == "Action_Mismatch": guidance_text += f"- Action Check: {a_g}\n"

            samples.append({
                "image_path": str(img_path), "test_type": test_type,
                "gt_tool": gt_tool, "gt_part": gt_part, "gt_action": gt_action,
                "fake_tool": fake_tool, "fake_part": fake_part, "fake_action": fake_action,
                "should_guide": should_guide, "guidance_text": guidance_text
            })
        except:
            continue

    results = []
    print(f"Round {round_idx}: Running {len(samples)} samples...")
    for s in tqdm(samples, leave=False):
        base_constraints = (
            f"Constraint 1 - Tools: [{TOOLS_PROMPT_STR}].\n"
            f"Constraint 2 - Actions: [{ACTIONS_PROMPT_STR}].\n"
            f"Constraint 3 - Parts: [{PARTS_PROMPT_STR}].\n\n"
            f"Output ONLY in this JSON format: {{\"action\": \"...\", \"tool\": \"...\", \"part\": \"...\", \"phase\": \"...\"}}."
        )

        # === A组: Baseline (标准) ===
        p_a = f"You are an assembly quality inspector. Observe this frame. Identify the hand action, tool, part, and phase.\n\n{base_constraints}"

        # === B组: Adversarial (降权 - Calibrated) ===
        # 修改点：将 "EXPECTS" 改为 "schedule suggests" (建议性语气)，并放在 Hint 中
        p_b = (
            f"You are an assembly quality inspector. Observe this frame. Identify the hand action, tool, part, and phase.\n\n"
            f"Hint: The system schedule lists the tool as [{s['fake_tool']}], part as [{s['fake_part']}], action as [{s['fake_action']}].\n"
            f"{base_constraints}")

        # === C组: Guided (判别性细节指导) ===
        if s['should_guide']:
            p_c = (
                f"You are an assembly quality inspector. Observe this frame. Identify the hand action, tool, part, and phase.\n\n"
                f"VISUAL ATTENTION CHECK (Critical for Distinguishing):\n"  # 修改标题
                f"{s['guidance_text']}\n"
                f"{base_constraints}")
        else:
            p_c = p_a

        res_a = run_vlm(model, processor, s['image_path'], p_a)
        res_b = run_vlm(model, processor, s['image_path'], p_b)
        res_c = run_vlm(model, processor, s['image_path'], p_c)

        tgt_gt = s['gt_tool']
        val_a, val_b, val_c = res_a.get('tool', ''), res_b.get('tool', ''), res_c.get('tool', '')

        if s['test_type'] == "Part_Mismatch":
            tgt_gt = s['gt_part']
            val_a, val_b, val_c = res_a.get('part', ''), res_b.get('part', ''), res_c.get('part', '')
        elif s['test_type'] == "Action_Mismatch":
            tgt_gt = s['gt_action']
            val_a, val_b, val_c = res_a.get('action', ''), res_b.get('action', ''), res_c.get('action', '')

        acc_a = (str(val_a).lower().strip() == str(tgt_gt).lower().strip())
        acc_b = (str(val_b).lower().strip() == str(tgt_gt).lower().strip())
        acc_c = (str(val_c).lower().strip() == str(tgt_gt).lower().strip())

        results.append({
            "Round": round_idx, "Type": s['test_type'], "Category": tgt_gt,
            "Acc A": acc_a, "Acc B": acc_b, "Acc C": acc_c,
            "Strategy": "Guided" if s['should_guide'] else "Baseline"
        })
    return results


# ================= 主程序 =================
def main():
    all_data = []
    for f in DATA_FILES:
        if f.exists(): all_data.extend(json.load(open(f)))

    model, processor = load_model()
    all_res = []

    print(f">>> 开始校准版 A/B/C 实验 (Calibrated, {NUM_ROUNDS} Rounds)...")
    for r in range(1, NUM_ROUNDS + 1):
        all_res.extend(run_single_round(r, model, processor, all_data))

    df = pd.DataFrame(all_res)
    df.to_csv(PROJECT_ROOT / "output" / "guided_abc_experiment_2_10" / "guided_abc_calibrated_raw.csv", index=False)

    # === 统计摘要 ===
    print("\n" + "=" * 60)
    print("📊 实验结果: 理想状态检查 (Ideal State Check)")
    print("=" * 60)

    overall_a = df['Acc A'].mean() * 100
    overall_b = df['Acc B'].mean() * 100
    overall_c = df['Acc C'].mean() * 100

    print(f"[总体准确率 Accuracy]")
    print(f"  A (Baseline):     {overall_a:.2f}%")
    print(f"  B (Adversarial):  {overall_b:.2f}%  (Target: ~50-60%)")
    print(f"  C (Guided):       {overall_c:.2f}%  (Target: > A)")
    print("-" * 60)

    # 细分榜单
    guided_df = df[df['Strategy'] == "Guided"]
    if len(guided_df) > 0:
        summary = guided_df.groupby("Category").agg(
            Count=('Category', 'count'),
            Acc_A=('Acc A', 'mean'),
            Acc_B=('Acc B', 'mean'),
            Acc_C=('Acc C', 'mean')
        ).reset_index()
        summary['Acc_A'] *= 100
        summary['Acc_B'] *= 100
        summary['Acc_C'] *= 100
        summary['Gain (C-A)'] = summary['Acc_C'] - summary['Acc_A']

        print(f"[弱项表现 (Weak Categories Performance)]")
        print(summary.sort_values("Gain (C-A)", ascending=False).to_string(index=False, float_format="%.1f"))
        summary.to_csv(PROJECT_ROOT / "output" / "guided_abc_experiment_2_10" / "guided_abc_calibrated_summary.csv", index=False)

    print("=" * 60)


if __name__ == "__main__":
    main()