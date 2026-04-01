import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from sklearn.metrics import confusion_matrix
import numpy as np
from pathlib import Path

# ================= 配置区域 =================
# 1. 设置路径
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent

# 2. 选择你要分析的结果文件 (Zero-shot 或 Few-shot)
CSV_FILE = PROJECT_ROOT / "output" / "evaluation_tools_zeroshot.csv"  # 选这个看 Zero-shot
# CSV_FILE = PROJECT_ROOT / "output" / "evaluation_results_fewshot.csv"  # 选这个看 Few-shot (根据你实际保存的名字修改)

# 3. 图片保存目录
SAVE_DIR = PROJECT_ROOT / "plots"/"tool_zeroshot"
SAVE_DIR.mkdir(exist_ok=True)


# ===========================================

def plot_confusion_matrix(df, target_col, pred_col, title, filename):
    """
    绘制并保存混淆矩阵
    :param df: 数据框
    :param target_col: 真实标签列名 (e.g., 'gt_tool')
    :param pred_col: 预测标签列名 (e.g., 'pred_tool')
    :param title: 图表标题
    :param filename: 保存的文件名
    """
    print(f"正在绘制: {title}...")

    # 1. 提取数据并清洗 (去掉空值和不规范的大小写)
    y_true = df[target_col].fillna("N/A").astype(str).str.title()  # 统一首字母大写
    y_pred = df[pred_col].fillna("N/A").astype(str).str.title()

    # 2. 获取所有唯一的标签 (让矩阵的行列对应)
    labels = sorted(list(set(y_true) | set(y_pred)))

    # 移除 'N/A' 标签（如果不想看 N/A 可以取消注释下面这行）
    # labels = [l for l in labels if l != "N/A"]

    # 3. 计算混淆矩阵
    cm = confusion_matrix(y_true, y_pred, labels=labels)

    # 4. 绘图设置
    plt.figure(figsize=(10, 8))  # 画布大小

    # 绘制热力图
    # annot=True: 显示数值
    # fmt='d': 显示整数 (如果你想显示百分比，需要先计算 normalize)
    # cmap='Blues': 颜色风格 (Blues, Greens, Oranges, Reds)
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                xticklabels=labels, yticklabels=labels,
                annot_kws={"size": 12})  # 数字字体大小

    plt.xlabel('Predicted Label', fontsize=12, fontweight='bold')
    plt.ylabel('True Label', fontsize=12, fontweight='bold')
    plt.title(title, fontsize=14, fontweight='bold')

    # 旋转 x 轴标签，防止重叠
    plt.xticks(rotation=45, ha='right')
    plt.yticks(rotation=0)
    plt.tight_layout()

    # 5. 保存
    save_path = SAVE_DIR / filename
    plt.savefig(save_path, dpi=300)  # dpi=300 适合论文打印
    print(f"已保存: {save_path}")
    plt.close()


def main():
    if not CSV_FILE.exists():
        print(f"错误: 找不到文件 {CSV_FILE}")
        return

    # 读取 CSV
    df = pd.read_csv(CSV_FILE)
    print(f"成功读取数据: {len(df)} 行")

    # 1. 绘制 Tool 混淆矩阵
    plot_confusion_matrix(
        df,
        target_col='gt_tool',
        pred_col='pred_tool',
        title='Confusion Matrix - Tool Recognition',
        filename='cm_tool.png'
    )

    # 2. 绘制 Action 混淆矩阵
    plot_confusion_matrix(
        df,
        target_col='gt_action',
        pred_col='pred_action',
        title='Confusion Matrix - Action Recognition',
        filename='cm_action.png'
    )

    # 3. 绘制 Part 混淆矩阵
    plot_confusion_matrix(
        df,
        target_col='gt_part',
        pred_col='pred_part',
        title='Confusion Matrix - Part Identification',
        filename='cm_part.png'
    )

    print("\n所有绘图完成！请查看 plots 文件夹。")


if __name__ == "__main__":
    main()