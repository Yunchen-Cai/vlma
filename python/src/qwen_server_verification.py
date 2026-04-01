import os
import time
import json
import queue
import threading
import traceback
import torch
import numpy as np
import cv2
from pathlib import Path
from flask import Flask, request, jsonify
from PIL import Image
from transformers import Qwen2_5_VLForConditionalGeneration, AutoProcessor, BitsAndBytesConfig
from peft import PeftModel

# ================= 动态路径配置 =================
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
PORT = 5005
BASE_MODEL_PATH = PROJECT_ROOT / "cache" / "huggingface" / "hub" / "Qwen2.5-VL-7B-Instruct"
LORA_PATH = PROJECT_ROOT / "output" / "v3.14_few_shot_verification"

# ================= 约束列表 =================
TOOLS_PROMPT_STR = "Hands, Hex Wrench, Screwdriver, Open End Wrench, adjustable wrench, Hammer"
PARTS_PROMPT_STR = "Mounting Flange, Gear Housing, Thrust Block, Drive Gear, Driven Gear, Port End Cover, Capscrew"
ACTIONS_PROMPT_STR = "Install, Tighten, Place, Insert"

# ================= 🌟 基于 Step 序号的 Verification Guidance Map =================
# 注意：这里的 key ("1", "2" 等) 需要和前端传过来的 X-Expect-Condition (step序号) 保持一致！
# ================= 🌟 极致精简版 Verification Guidance Map =================
STEP_GUIDANCE_MAP = {
    "2": "222",
    "4": "444",
    "6": "",
    "7": ""
}

# ================= 全局变量 =================
app = Flask(__name__)
image_queue = queue.Queue(maxsize=100)
result_queue = queue.Queue()
model = None
processor = None


# ================= 核心函数 =================

def load_qwen_model():
    global model, processor
    print(f">>> [1/3] 正在加载基座模型 (4-bit 量化模式)...")
    try:
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.bfloat16
        )
        model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
            str(BASE_MODEL_PATH), quantization_config=bnb_config, device_map="cuda",
        )
        if LORA_PATH and LORA_PATH.exists():
            print(f">>> [2/3] 挂载 LoRA...")
            model = PeftModel.from_pretrained(model, str(LORA_PATH))
        processor = AutoProcessor.from_pretrained(str(BASE_MODEL_PATH))
        print(f"✅ [3/3] 模型加载完成！")
    except Exception as e:
        print(f"❌ 模型加载失败:\n{traceback.format_exc()}")


def extract_json(text):
    try:
        return json.loads(text)
    except:
        try:
            start, end = text.find('{'), text.rfind('}')
            if start != -1 and end != -1: return json.loads(text[start:end + 1])
        except:
            pass
    return {}


# 🌟 修改点：将 prompt_text 作为参数传入，由 Worker 根据交替逻辑动态生成
def run_inference(image_np, prompt_text):
    global model, processor

    image_rgb = cv2.cvtColor(image_np, cv2.COLOR_BGR2RGB)
    pil_image = Image.fromarray(image_rgb).resize((448, 448), Image.Resampling.LANCZOS)

    messages = [
        {"role": "user", "content": [{"type": "image", "image": pil_image}, {"type": "text", "text": prompt_text}]}]
    text_input = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = processor(text=[text_input], images=[pil_image], padding=True, return_tensors="pt").to(model.device)

    with torch.no_grad():
        outputs = model.generate(**inputs, max_new_tokens=256, return_dict_in_generate=True, output_scores=True)

    transition_scores = model.compute_transition_scores(outputs.sequences, outputs.scores, normalize_logits=True)
    linear_probs = np.exp(transition_scores[0].cpu().numpy())
    confidence_score = float(np.mean(linear_probs))

    input_len = inputs.input_ids.shape[1]
    generated_ids_trimmed = outputs.sequences[:, input_len:]
    output_text = processor.batch_decode(generated_ids_trimmed, skip_special_tokens=True)[0]

    return extract_json(output_text), output_text, confidence_score


# ================= Worker =================

def worker_thread():
    print(">>> Worker 线程就绪...")
    frame_counter = 0

    while True:
        try:
            task = image_queue.get()
            if task is None: break

            req_id, img_np, condition_step = task
            start_time = time.time()
            frame_counter += 1
            # 🌟 加上这行核对前端传来的到底是个什么鬼东西！
            print(f"\n👉 [DEBUG - 前端传来的 condition_step]: '{condition_step}'")

            result_final = {}
            if model:
                try:
                    is_target_step = condition_step in STEP_GUIDANCE_MAP
                    use_guided = is_target_step and (frame_counter % 2 == 0)

                    if use_guided:
                        # 🔵 触发深度核查 (Guided Prompt)
                        rule = STEP_GUIDANCE_MAP[condition_step]
                        prompt_text = (
                            f"You are an assembly quality inspector evaluating step {condition_step}.\n\n"
                            f"{rule}\n\n"
                            f"First, explain your visual observation. Then, strictly output your final conclusion in JSON format: "
                            f"{{\"verification\": \"finish/unfinish\"}}."  # 🌟 极致精简：只要求输出 verification
                        )
                        frame_type_log = "Guided"
                    else:
                        # 🟢 触发基础识别 (General Prompt)
                        prompt_text = (
                            f"You are an assembly quality inspector. Observe this frame. Identify the hand action, tool, and part.\n\n"
                            f"Constraint 1 - Tools: The tool must be chosen from: [{TOOLS_PROMPT_STR}].\n"
                            f"Constraint 2 - Actions: The action must be chosen from: [{ACTIONS_PROMPT_STR}].\n"
                            f"Constraint 3 - Parts: The part must be chosen from: [{PARTS_PROMPT_STR}].\n\n"
                            f"Output ONLY in this JSON format: "
                            f"{{\"action\": \"...\", \"tool\": \"...\", \"part\": \"...\"}}."  # 🌟 极致精简：只要求输出分类
                        )
                        frame_type_log = "General"

                    # 执行推理
                    pred_json, raw_text, confidence = run_inference(img_np, prompt_text)

                    # ==========================================
                    # 🌟 核心修改点：根据 frame_type 强行覆盖输出值
                    # ==========================================
                    if use_guided:
                        # 1. Guided 模式下：提取 verification，其他全部强制为 "N/A"
                        model_verification = pred_json.get("verification", "unknown")
                        detected_action = "N/A"
                        detected_tool = "N/A"
                        detected_part = "N/A"
                    else:
                        # 2. General 模式下：提取分类参数，verification 强制为 "unfinish"
                        model_verification = "N/A"
                        detected_action = pred_json.get("action", "Unknown")
                        detected_tool = pred_json.get("tool", "Unknown")
                        detected_part = pred_json.get("part", "Unknown")

                    reason = "Inference Successful"
                    if confidence < 0.60:
                        reason += f" [Warning: Low Confidence {confidence:.2f}]"

                    # 🌟 加上这行专属日志，只看 verification 到底提取到了什么！
                    print(f"\n👉 [DEBUG - 当前帧提取的 Verification 状态]: {model_verification}")
                    # 统一返回给前端的数据结构
                    result_final = {
                        "verification": model_verification == "finish",
                        "tool": detected_tool,
                        "action": detected_action,
                        "part": detected_part,
                        "confidence": f"{confidence:.4f}",
                        "reason": reason
                    }

                except Exception as infer_err:
                    print(f"❌ 推理错误: {traceback.format_exc()}")
                    result_final = {"error": str(infer_err)}

            fps = 1.0 / (time.time() - start_time)
            result_final.setdefault('_meta', {})['fps'] = f"{fps:.2f}"
            result_final.setdefault('_meta', {})['req_id'] = req_id

            # 打印日志
            print(
                f"[完成] ID:{req_id} TYPE:{result_final.get('frame_type')} FPS:{fps:.2f} Conf:{result_final.get('confidence')} | Veri:{result_final.get('verification')} | Tool:{result_final.get('tool')} | Part:{result_final.get('part')}")
            result_queue.put(result_final)

        except Exception as e:
            print(f"❌ Worker错误: {traceback.format_exc()}")


# ================= API =================

@app.route('/process_image', methods=['POST'])
def process_image():
    try:
        if image_queue.full(): return jsonify({"status": "busy"}), 503

        image_data = request.data
        nparr = np.frombuffer(image_data, np.uint8)
        img_np = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        # 🌟 核心修改点：只接收前端的 step 序号
        condition_step = request.headers.get('X-Expect-Condition', '')

        # print("👉 [DEBUG - Raw Headers]", dict(request.headers))
        print(f"👉 [DEBUG - X-Expect-Condition] '{request.headers.get('X-Expect-Condition')}'")

        req_id = int(time.time() * 1000)
        # 将 step 序号送入队列
        image_queue.put((req_id, img_np, condition_step))

        result = result_queue.get(timeout=600)
        return jsonify(result)

    except Exception as e:
        print(f"❌ API错误: {traceback.format_exc()}")
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    load_qwen_model()
    t = threading.Thread(target=worker_thread, daemon=True)
    t.start()
    app.run(host='0.0.0.0', port=PORT, threaded=True)