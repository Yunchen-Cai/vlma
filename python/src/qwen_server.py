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
from transformers import Qwen2_5_VLForConditionalGeneration, AutoProcessor, BitsAndBytesConfig  # <--- 引入这个
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
        # === 关键修改：开启 4-bit 量化 ===
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.bfloat16
        )

        model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
            str(BASE_MODEL_PATH),
            quantization_config=bnb_config,  # <--- 强制量化
            device_map="cuda",  # <--- 强制 GPU
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
            start = text.find('{')
            end = text.rfind('}')
            if start != -1 and end != -1:
                return json.loads(text[start:end + 1])
        except:
            pass
    return {}


def run_inference(image_np):
    global model, processor

    # ... (前面的 Prompt 和 图片预处理代码保持完全不变) ...
    # 为了节省篇幅，这里假设 prompt_text, pil_image, inputs 已经准备好了
    # ------------------------------------------------------------------

    # 1. 构造 Prompt (保持不变)
    prompt_text = (
        f"You are an assembly quality inspector. Observe this frame. "
        f"Identify the hand action, tool, part, and phase.\n\n"
        f"Constraint 1 - Tools: The tool must be chosen from: [{TOOLS_PROMPT_STR}].\n"
        f"Constraint 2 - Actions: The action must be chosen from: [{ACTIONS_PROMPT_STR}].\n"
        f"Constraint 3 - Parts: The part must be chosen from: [{PARTS_PROMPT_STR}].\n\n"
        f"Output ONLY in this JSON format: "
        f"{{\"action\": \"...\", \"tool\": \"...\", \"part\": \"...\", \"phase\": \"...\"}}."
    )

    # 2. 图片处理 (保持不变)
    image_rgb = cv2.cvtColor(image_np, cv2.COLOR_BGR2RGB)
    pil_image = Image.fromarray(image_rgb)
    pil_image = pil_image.resize((448, 448), Image.Resampling.LANCZOS)

    # 3. 准备输入 (保持不变)
    messages = [
        {"role": "user", "content": [{"type": "image", "image": pil_image}, {"type": "text", "text": prompt_text}]}]
    text_input = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = processor(text=[text_input], images=[pil_image], padding=True, return_tensors="pt").to(model.device)

    # ------------------------------------------------------------------
    # === 核心修改点：开启分数计算 ===
    # ------------------------------------------------------------------
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=128,
            return_dict_in_generate=True,  # 必须：告诉模型把详细数据交出来
            output_scores=True  # 必须：要求返回每一步的 Logits
        )

    # 1. 计算转换分数 (Log Probability)
    # 这会提取出模型生成的每一个 Token 的 log(概率)
    transition_scores = model.compute_transition_scores(
        outputs.sequences, outputs.scores, normalize_logits=True
    )

    # 2. 数学转换：Log概率 -> 线性概率 (0~1)
    # exp(-0.01) = 0.99
    # transition_scores[0] 代表 Batch 里的第一张图
    log_probs = transition_scores[0].cpu().numpy()
    linear_probs = np.exp(log_probs)

    # 3. 计算整句话的平均置信度
    # 过滤掉特殊的 Padding Token (如果有的话)，通常取平均值即可
    confidence_score = float(np.mean(linear_probs))

    # ------------------------------------------------------------------

    # 4. 截断 Prompt，只留输出 (保持不变)
    input_len = inputs.input_ids.shape[1]
    generated_ids_trimmed = outputs.sequences[:, input_len:]
    output_text = processor.batch_decode(generated_ids_trimmed, skip_special_tokens=True)[0]

    return extract_json(output_text), output_text, confidence_score


# ================= Worker =================

def worker_thread():
    print(">>> Worker 线程就绪...")
    while True:
        try:
            task = image_queue.get()
            if task is None: break

            req_id, img_np, expectations = task
            start_time = time.time()

            result_final = {}
            if model:
                try:
                    # === 接收 3 个返回值：JSON, 原始文本, 置信度 ===
                    pred_json, raw_text, confidence = run_inference(img_np)

                    verification = True
                    reason = "Matches SOP"

                    detected_tool = pred_json.get("tool", "Unknown")
                    detected_action = pred_json.get("action", "Unknown")

                    exp_tool = expectations.get('tool')
                    exp_action = expectations.get('action')

                    # 验证逻辑
                    if exp_tool and (exp_tool.lower() not in detected_tool.lower()):
                        verification = False
                        reason = f"Tool Mismatch: Expected '{exp_tool}', saw '{detected_tool}'"
                    elif exp_action and (exp_action.lower() not in detected_action.lower()):
                        verification = False
                        reason = f"Action Mismatch: Expected '{exp_action}', saw '{detected_action}'"

                    # === 核心：如果置信度太低，强制标记为 Warning ===
                    # 比如：虽然名字对上了，但模型其实是瞎猜的（概率只有 40%）
                    confidence_threshold = 0.60  # 60% 以下视为不可信
                    if confidence < confidence_threshold:
                        reason += f" [Warning: Low Confidence {confidence:.2f}]"
                        # 你甚至可以在这里把 verification 强制设为 False
                        # verification = False

                    result_final = {
                        "verification": verification,
                        "tool": detected_tool,
                        "action": detected_action,
                        "part": pred_json.get("part", "Unknown"),
                        "confidence": f"{confidence:.4f}",  # <--- 输出给客户端
                        "reason": reason
                    }
                except Exception as infer_err:
                    print(f"❌ 推理错误: {traceback.format_exc()}")
                    result_final = {"error": str(infer_err)}

            fps = 1.0 / (time.time() - start_time)
            result_final.setdefault('_meta', {})['fps'] = f"{fps:.2f}"
            result_final.setdefault('_meta', {})['req_id'] = req_id

            # 打印日志里也显示置信度
            print(
                f"[完成] ID:{req_id} FPS:{fps:.2f} Conf:{result_final.get('confidence')} | Veri:{result_final.get('verification')}")
            result_queue.put(result_final)

        except Exception as e:
            print(f"❌ Worker错误: {traceback.format_exc()}")


# ================= API =================

@app.route('/process_image', methods=['POST'])
def process_image():
    print(image_queue.qsize())
    try:
        if image_queue.full(): return jsonify({"status": "busy"}), 503
        image_data = request.data
        nparr = np.frombuffer(image_data, np.uint8)
        img_np = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        expectations = {
            "tool": request.headers.get('X-Expect-Tool'),
            "action": request.headers.get('X-Expect-Action')
        }

        req_id = int(time.time() * 1000)
        image_queue.put((req_id, img_np, expectations))

        # 增加超时到 60秒 (为了第一次预热)，平时应该很快
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