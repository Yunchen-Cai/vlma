import cv2
import torch
import json
import time
import re
from pathlib import Path
from PIL import Image
from collections import deque, Counter
from transformers import Qwen2_5_VLForConditionalGeneration, AutoProcessor, BitsAndBytesConfig  # <--- 引入这个
from peft import PeftModel

# ================= 配置区域 =================
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
OUTPUT_DIR = PROJECT_ROOT / "output" / "v1.23_new_simple"  # 指向你训练好的 output 目录
VIDEO_INPUT = r"D:\vlm_assembly\data\standard_videos\screwdriver.mp4"  # 输入视频路径
VIDEO_OUTPUT = PROJECT_ROOT / "output" / "result2_screwdriver.mp4"  # 输出视频路径
EXTENDED_ALLOWED_TOOLS = [
    "Hands",
    "Hex Wrench",
    "Screwdriver",
    "Open End Wrench",
    "adjustable wrench",
    "Hammer"
]
# 允许的零件列表
ALLOWED_PARTS = [
    "Mounting Flange", "Gear Housing", "Thrust Block",
    "Drive Gear", "Driven Gear", "Port End Cover", "Capscrew"
]

# 推理设置
CHECK_INTERVAL = 10
WINDOW_SIZE = 10

tools_str = ", ".join(EXTENDED_ALLOWED_TOOLS)
parts_str = ", ".join(ALLOWED_PARTS)

# ===========================================

# ... (AssemblyStateTracker 类保持不变，请保留) ...
class AssemblyStateTracker:
    # ... (把上面的 AssemblyStateTracker 代码保留在这里) ...
    def __init__(self, window_size=5):
        self.window_size = window_size
        self.action_buffer = deque(maxlen=window_size)
        self.part_buffer = deque(maxlen=window_size)
        self.phase_buffer = deque(maxlen=window_size)

        self.confirmed_action = "Detecting..."
        self.confirmed_part = "None"
        self.confirmed_phase = "N/A"
        self.confirmed_tool = "N/A"
        self.last_valid_part = "None"

    def update(self, raw_result):
        raw_action = raw_result.get("action", "Unknown")
        raw_part = raw_result.get("part", "Unknown")
        raw_phase = raw_result.get("phase", "Unknown")
        raw_tool = raw_result.get("tool", "Unknown")

        self.action_buffer.append(raw_action)
        self.part_buffer.append(raw_part)
        self.phase_buffer.append(raw_phase)

        action_counts = Counter(self.action_buffer)
        part_counts = Counter(self.part_buffer)

        most_common_action, action_count = action_counts.most_common(1)[0]

        if action_count >= (self.window_size / 2):
            self.confirmed_action = most_common_action

        most_common_part, part_count = part_counts.most_common(1)[0]

        if most_common_part in ALLOWED_PARTS:
            self.last_valid_part = most_common_part
            self.confirmed_part = most_common_part
        else:
            if self.confirmed_action in ["Insert", "Tighten", "Place", "Install"]:
                self.confirmed_part = self.last_valid_part
            else:
                self.confirmed_part = most_common_part

        self.confirmed_phase = Counter(self.phase_buffer).most_common(1)[0][0]
        self.confirmed_tool = raw_tool

        return {
            "action": self.confirmed_action,
            "part": self.confirmed_part,
            "phase": self.confirmed_phase,
            "tool": self.confirmed_tool
        }


# ================= 核心修改：加载模型时启用 4-bit 量化 =================
def load_model():
    print(f"Loading Base Model (4-bit)...")
    base_model_path = r"D:\vlm_assembly\cache\huggingface\hub\Qwen2.5-VL-7B-Instruct"

    # 1. 配置 4-bit 量化 (显存占用从 16G 降到 6G)
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
    )

    # 2. 加载基座
    model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
        base_model_path,
        quantization_config=bnb_config,  # 启用量化
        device_map="auto",
    )

    # 3. 限制输入分辨率 (防止 Token 爆炸)
    # min_pixels 和 max_pixels 限制图片处理大小
    processor = AutoProcessor.from_pretrained(
        base_model_path,
        min_pixels=224 * 224,
        max_pixels=448 * 448
    )

    print(f"Loading LoRA: {OUTPUT_DIR}")
    model = PeftModel.from_pretrained(model, OUTPUT_DIR)
    model.eval()
    return model, processor


def parse_response(response_text):
    try:
        clean_text = re.sub(r"```json|```", "", response_text).strip()
        data = json.loads(clean_text)
        return data
    except:
        return {"action": "Unknown", "part": "Unknown", "phase": "Unknown"}


def draw_info(frame, info, fps):
    overlay = frame.copy()
    cv2.rectangle(overlay, (20, 20), (550, 270), (0, 0, 0), -1)
    alpha = 0.6
    cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)

    font = cv2.FONT_HERSHEY_SIMPLEX
    act = info.get('action', 'N/A')
    color = (0, 255, 0)
    if "Insert" in act: color = (255, 200, 0)
    if "Tighten" in act: color = (0, 0, 255)

    cv2.putText(frame, f"Action: {act}", (40, 70), font, 1.2, color, 3)
    cv2.putText(frame, f"Part:   {info.get('part', 'N/A')}", (40, 120), font, 1.0, (0, 255, 255), 2)
    cv2.putText(frame, f"Tool:   {info.get('tool', 'N/A')}", (40, 165), font, 1.0, (255, 0, 255), 2)
    cv2.putText(frame, f"Phase:  {info.get('phase', 'N/A')}", (40, 210), font, 0.8, (255, 255, 255), 1)
    cv2.putText(frame, f"FPS:    {fps:.1f}", (40, 250), font, 0.8, (200, 200, 200), 1)

def main():
    model, processor = load_model()
    cap = cv2.VideoCapture(VIDEO_INPUT)

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    out = cv2.VideoWriter(str(VIDEO_OUTPUT), cv2.VideoWriter_fourcc(*'mp4v'), fps, (width, height))

    tracker = AssemblyStateTracker(window_size=WINDOW_SIZE)

    frame_count = 0
    start_time = time.time()

    current_smooth_result = {"action": "Init...", "part": "None", "phase": "N/A"}

    print("🚀 开始极速推理...")

    while True:
        ret, frame = cap.read()
        if not ret: break

        if frame_count % CHECK_INTERVAL == 0:
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(rgb_frame)

            # === 核心修改：调整图片大小 ===
            # 不要把 1080p 的大图直接扔进去，先缩小到合理尺寸
            # 保持长宽比，最大边长 720
            pil_image.thumbnail((448, 448))

            prompt_text = (
                f"You are a visual recognition system. Analyze the current frame strictly based on visual appearance.\n"
                f"Identify the hand action, tool, part, and phase.\n\n"
                f"Standard Parts: [{parts_str}]\n"
                f"Available Tools: [{tools_str}]\n\n"
                f"INSTRUCTION:\n"
                f"1. Look closely at the object in the hand. Distinguish between a Hex Wrench (L-shaped), a Screwdriver (straight handle), a Hammer, and a Wrench.\n"
                f"2. Report exactly what you see from the 'Available Tools' list. Do NOT guess based on the assembly context.\n"
                f"3. If the tool looks like a Screwdriver or Hammer, output that specific name, even if it is unusual.\n\n"
                f"Output ONLY in this JSON format: "
                f"{{\"action\": \"...\", \"tool\": \"...\", \"part\": \"...\", \"phase\": \"...\"}}."
            )

            messages = [{"role": "user",
                         "content": [{"type": "image", "image": pil_image}, {"type": "text", "text": prompt_text}]}]
            text_input = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
            inputs = processor(text=[text_input], images=[pil_image], padding=True, return_tensors="pt").to(
                model.device)

            with torch.no_grad():
                generated_ids = model.generate(**inputs, max_new_tokens=64)
                output_text = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
                if "assistant\n" in output_text:
                    output_text = output_text.split("assistant\n")[-1]

            raw_result = parse_response(output_text)
            current_smooth_result = tracker.update(raw_result)

            # 计算瞬时 FPS
            elapsed = time.time() - start_time
            print(
                f"Frame {frame_count} | FPS: {frame_count / (elapsed + 0.01):.1f} | Result: {current_smooth_result['action']} - {current_smooth_result['part']}")

        current_fps = frame_count / (time.time() - start_time + 0.001)
        draw_info(frame, current_smooth_result, current_fps)

        out.write(frame)
        cv2.imshow('Robust Inspector', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'): break
        frame_count += 1

    cap.release()
    out.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()