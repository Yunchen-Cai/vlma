import pandas as pd
import numpy as np
from pathlib import Path

# ================= 配置区域 =================
# 1. 设置路径
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent

# 2. 输入文件路径
FILE_ZERO = PROJECT_ROOT / "output" / "evaluation_results_zeroshot.csv"
FILE_FEW = PROJECT_ROOT / "output" / "evaluation_results_fewshot.csv"

# 3. 输出表格保存路径
OUTPUT_EXCEL = PROJECT_ROOT / "output" / "accuracy_comparison_report.xlsx"


# ===========================================

def calculate_per_class_accuracy(df, gt_col, pred_col):
    """
    计算每个类别的准确率 (Recall: 该类别的样本有多少被正确识别)
    """
    # 统一大小写，填充空值
    y_true = df[gt_col].fillna("N/A").astype(str).str.title()
    y_pred = df[pred_col].fillna("N/A").astype(str).str.title()

    # 获取所有类别
    classes = y_true.unique()

    stats = []
    for cls in classes:
        # 找出真实标签为 cls 的所有行
        mask = (y_true == cls)
        total = mask.sum()

        if total == 0:
            continue

        # 在这些行中，预测正确的数量
        correct = (y_pred[mask] == cls).sum()
        acc = correct / total

        stats.append({
            "Class": cls,
            "Count": total,
            "Correct": correct,
            "Accuracy": acc
        })

    return pd.DataFrame(stats).set_index("Class")


def main():
    # 1. 检查文件是否存在
    if not FILE_ZERO.exists() or not FILE_FEW.exists():
        print("错误: 找不到输入 CSV 文件。请确保 evaluation_results_zeroshot.csv 和 fewshot.csv 都已生成。")
        return

    # 2. 读取数据
    df_zero = pd.read_csv(FILE_ZERO)
    df_few = pd.read_csv(FILE_FEW)

    print(f"Zero-shot 样本数: {len(df_zero)}")
    print(f"Few-shot  样本数: {len(df_few)}")

    # ==========================================
    # Part 1: 总体准确率对比 (Overall Accuracy)
    # ==========================================
    overall_stats = []

    for task in ['tool', 'action', 'part']:
        col = f'{task}_correct'
        acc_zero = df_zero[col].mean()
        acc_few = df_few[col].mean()
        gap = acc_few - acc_zero

        overall_stats.append({
            "Task": task.capitalize(),
            "Zero-shot Acc": f"{acc_zero:.2%}",
            "Few-shot Acc": f"{acc_few:.2%}",
            "Improvement": f"+{gap:.2%}"
        })

    df_overall = pd.DataFrame(overall_stats)
    print("\n=== Overall Accuracy Comparison ===")
    print(df_overall)

    # ==========================================
    # Part 2: 细分准确率对比 (Per-Class Accuracy)
    # ==========================================

    def get_comparison_table(target_col, pred_col, type_name):
        # 分别计算
        stats_zero = calculate_per_class_accuracy(df_zero, target_col, pred_col)
        stats_few = calculate_per_class_accuracy(df_few, target_col, pred_col)

        # 合并
        merged = stats_zero[['Accuracy']].join(stats_few[['Accuracy']], lsuffix='_zero', rsuffix='_few', how='outer')

        # 格式化
        # 如果是 NaN (说明该数据集里没有这个类), 填 0
        merged = merged.fillna(0)

        merged['Zero-shot'] = merged['Accuracy_zero'].apply(lambda x: f"{x:.2%}")
        merged['Few-shot'] = merged['Accuracy_few'].apply(lambda x: f"{x:.2%}")
        merged['Improvement'] = (merged['Accuracy_few'] - merged['Accuracy_zero']).apply(lambda x: f"{x:+.2%}")

        return merged[['Zero-shot', 'Few-shot', 'Improvement']]

    # 生成三张细分表
    df_tool_comp = get_comparison_table('gt_tool', 'pred_tool', 'Tool')
    df_action_comp = get_comparison_table('gt_action', 'pred_action', 'Action')
    df_part_comp = get_comparison_table('gt_part', 'pred_part', 'Part')

    print("\n=== Tool Accuracy Comparison ===")
    print(df_tool_comp)

    # ==========================================
    # Part 3: 保存到 Excel (方便复制到论文)
    # ==========================================
    OUTPUT_EXCEL.parent.mkdir(parents=True, exist_ok=True)

    with pd.ExcelWriter(OUTPUT_EXCEL) as writer:
        df_overall.to_excel(writer, sheet_name='Overall Summary', index=False)
        df_tool_comp.to_excel(writer, sheet_name='Tool Breakdown')
        df_action_comp.to_excel(writer, sheet_name='Action Breakdown')
        df_part_comp.to_excel(writer, sheet_name='Part Breakdown')

    print(f"\n所有统计表格已保存至: {OUTPUT_EXCEL}")


if __name__ == "__main__":
    main()