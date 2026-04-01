import torch
import os
import sys
from pathlib import Path
from PIL import Image
from transformers import Qwen2_5_VLForConditionalGeneration, AutoProcessor
from peft import PeftModel

# ================= 配置区域 =================
# 1. 自动定位路径
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
HF_CACHE = PROJECT_ROOT / "cache" / "huggingface"
os.environ["HF_HOME"] = str(HF_CACHE)

# 模型路径
BASE_MODEL_PATH = r"D:\vlm_assembly\cache\huggingface\hub\Qwen2.5-VL-7B-Instruct"
ADAPTER_PATH = PROJECT_ROOT / "output" / "v12.23_focused_simple"

# 图片默认搜索路径 (根据您的描述)
# 脚本会自动去 D:\vlm_assembly\data\temp_frames 下找图片
DEFAULT_IMAGE_DIR = PROJECT_ROOT / "data" / "temp_frames_12.23merged"


# ===========================================

def load_model():
    """只运行一次：加载模型到显存"""
    print("\n" + "=" * 40)
    print("🚀 正在初始化系统...")
    print(f"1. 加载基座模型: {BASE_MODEL_PATH}")

    # 使用 4bit 加载，速度快且省显存
    model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
        BASE_MODEL_PATH,
        device_map="auto",
        load_in_4bit=True,
        trust_remote_code=True
    )

    print(f"2. 挂载 LoRA 权重: {ADAPTER_PATH}")
    # 加载微调后的权重
    try:
        model = PeftModel.from_pretrained(model, str(ADAPTER_PATH))
    except Exception as e:
        print(f"⚠️ 警告: 加载 LoRA 失败，将使用纯基座模型。错误: {e}")

    print("3. 加载处理器...")
    processor = AutoProcessor.from_pretrained(BASE_MODEL_PATH, trust_remote_code=True)

    print("✅ 系统就绪！等待输入...")
    print("=" * 40 + "\n")
    return model, processor


def run_inference_loop(model, processor):
    """进入无限循环，等待用户输入"""

    print(f"📂 默认图片目录: {DEFAULT_IMAGE_DIR}")
    print("💡 提示: 输入文件名即可 (例如: 202512121915_step1_frame_2.jpg)")
    print("❌ 退出: 输入 'exit' 或 'q'")

    while True:
        # 1. 获取用户输入
        filename = input("\n>>> 请输入图片文件名: ").strip()

        # 退出条件
        if filename.lower() in ['exit', 'quit', 'q', '退出']:
            print("👋 再见！")
            break

        if not filename:
            continue

        # 2. 智能构建路径
        # 如果用户直接粘贴了绝对路径 (D:\...)，就用绝对路径
        # 如果只输入了文件名，就拼接到默认目录
        if os.path.isabs(filename):
            image_path = Path(filename)
        else:
            image_path = DEFAULT_IMAGE_DIR / filename

        # 3. 检查文件是否存在
        if not image_path.exists():
            print(f"❌ 错误: 找不到文件 -> {image_path}")
            print(f"   请确认文件在 {DEFAULT_IMAGE_DIR} 下，或输入绝对路径。")
            continue

        try:
            # 4. 加载图片
            image = Image.open(image_path).convert("RGB")
            print(f"📸 正在分析: {image_path.name} ...")

            # 5. 构造 Prompt (必须与训练时完全一致)
            prompt_text = "You are an assembly quality inspector. Observe this frame. Identify the hand action, tool, part, and phase.\n\nAllowed Parts: [\"Mounting Flange\", \"Gear Housing\", \"Thrust Block\", \"Drive Gear\", \"Driven Gear\", \"Port End Cover\", \"Capscrew\"]\n\nOutput ONLY in this JSON format: {\"action\": \"...\", \"tool\": \"...\", \"part\": \"...\", \"phase\": \"...\"}."

            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "image", "image": image},
                        {"type": "text", "text": prompt_text},
                    ],
                }
            ]

            # 6. 处理输入
            text = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
            inputs = processor(
                text=[text],
                images=[image],
                padding=True,
                return_tensors="pt",
            )
            inputs = inputs.to("cuda")

            # 7. 模型生成
            with torch.no_grad():
                generated_ids = model.generate(
                    **inputs,
                    max_new_tokens=256,
                    temperature=0.1,  # 低温，保证输出稳定
                    top_p=0.9
                )

            # 8. 解码并输出
            generated_ids_trimmed = [
                out_ids[len(in_ids):] for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
            ]
            output_text = processor.batch_decode(
                generated_ids_trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False
            )[0]

            print("-" * 20 + " 模型输出 " + "-" * 20)
            print(output_text)
            print("-" * 50)

        except Exception as e:
            print(f"❌ 推理过程出错: {e}")


if __name__ == "__main__":
    # 1. 启动时加载一次
    model_instance, processor_instance = load_model()

    # 2. 进入交互循环
    run_inference_loop(model_instance, processor_instance)