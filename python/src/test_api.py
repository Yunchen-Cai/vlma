import requests
import os

# === 配置 ===
API_URL = "http://127.0.0.1:5005/process_image"

# 请替换成你电脑里真实存在的一张测试图片路径
TEST_IMAGE_PATH = r"D:\vlm_assembly\data\temp_frames_12.23merged\vid0_step3_frame1115.jpg"


def test_api():
    if not os.path.exists(TEST_IMAGE_PATH):
        print(f"❌ 找不到图片: {TEST_IMAGE_PATH}")
        return

    print(f">>> 正在发送图片: {TEST_IMAGE_PATH}")

    # 读取图片
    with open(TEST_IMAGE_PATH, "rb") as f:
        img_data = f.read()

    # 模拟 SM 指令
    headers = {
        "X-Expect-Tool": "hands",
        "X-Expect-Action": "place"
    }

    print(f">>> 发送指令: {headers}")

    try:
        # 发送请求 (这一步极快，因为不加载模型，只发 HTTP 包)
        response = requests.post(API_URL, data=img_data, headers=headers)

        if response.status_code == 200:
            print("\n✅ 成功！服务端返回 JSON：")
            print(json.dumps(response.json(), indent=2, ensure_ascii=False))
        else:
            print(f"\n❌ 失败 (Code {response.status_code}):")
            print(response.text)

    except Exception as e:
        print(f"\n❌ 连接错误: {e}")
        print("请检查 qwen_server.py 是否已启动？")


if __name__ == "__main__":
    import json

    test_api()