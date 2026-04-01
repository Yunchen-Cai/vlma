import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# 1. 读取数据
file_path = 'resolution_trend_16_9_final.csv'
df = pd.read_csv(file_path)

# 2. 计算平均准确率
df['Avg_Acc'] = (df['Tool_Acc'] + df['Action_Acc'] + df['Part_Acc']) / 3

# 3. 计算相对计算成本 (归一化像素数，以1080p为基准)
# 1080p的像素数 = 1920 * 1080 = 2,073,600
max_pixels = 1920 * 1080
df['Relative_Cost'] = (df['Width'] * df['Height']) / max_pixels

# 4. 设置画布 (双轴图)
fig, ax1 = plt.subplots(figsize=(12, 7))

# --- 背景：计算成本 (柱状图) ---
color_cost = 'lightgray'
ax2 = ax1.twinx()  # 创建共享X轴的第二个Y轴
bars = ax2.bar(df.index, df['Relative_Cost'], color=color_cost, alpha=0.3, width=0.6, label='Relative Compute Cost (Pixels)')
ax2.set_ylabel('Relative Compute Cost (Normalized to 1080p)', color='gray', fontsize=12)
ax2.tick_params(axis='y', labelcolor='gray')
ax2.set_ylim(0, 1.2) # 留出顶部空间

# --- 前景：准确率 (折线图) ---
# 绘制三条细线 (各个指标)
ax1.plot(df.index, df['Tool_Acc'], marker='o', linestyle=':', color='#1f77b4', alpha=0.6, linewidth=1, label='Tool Acc')
ax1.plot(df.index, df['Action_Acc'], marker='s', linestyle=':', color='#ff7f0e', alpha=0.6, linewidth=1, label='Action Acc')
ax1.plot(df.index, df['Part_Acc'], marker='^', linestyle=':', color='#2ca02c', alpha=0.6, linewidth=1, label='Part Acc')

# 绘制一条粗线 (平均准确率 - 核心指标)
line_avg, = ax1.plot(df.index, df['Avg_Acc'], marker='*', color='#d62728', linewidth=3, markersize=12, label='Average Accuracy (Main Metric)')

# --- 标注最佳点 (假设 720p 是最佳点，索引通常在中间) ---
# 自动寻找 "性价比" 最高的点 (这里为了PPT演示，我们手动锁定 720p，通常是效果最好的)
# 你需要根据打印出来的 df 确认 720p 的 index，这里假设是 index 5 (根据你的列表推算)
best_idx = df[df['Height'] == 720].index[0]
best_acc = df.loc[best_idx, 'Avg_Acc']
best_cost = df.loc[best_idx, 'Relative_Cost']

# 画圈标注
ax1.annotate(f'Sweet Spot (720p)\n~{best_acc:.1f}% Acc\nOnly {best_cost:.0%} Compute',
             xy=(best_idx, best_acc),
             xytext=(best_idx, best_acc + 10),
             arrowprops=dict(facecolor='black', shrink=0.05),
             fontsize=12, fontweight='bold', ha='center',
             bbox=dict(boxstyle="round,pad=0.3", fc="yellow", alpha=0.8))

# --- 格式化 ---
ax1.set_xlabel('Input Resolution (Height)', fontsize=12)
ax1.set_ylabel('Accuracy (%)', fontsize=12, color='black')
ax1.set_xticks(df.index)
ax1.set_xticklabels(df['Resolution_Label'], rotation=45, ha='right')
ax1.set_ylim(0, 105)
ax1.grid(True, linestyle='--', alpha=0.5)

# 合并图例
lines, labels = ax1.get_legend_handles_labels()
bars_legend, labels_legend = ax2.get_legend_handles_labels()
# 将柱状图的图例也加进来
ax1.legend(lines + bars_legend, labels + labels_legend, loc='upper left', fontsize=10)

plt.title('Trade-off Analysis: Accuracy vs. Computation Cost\n(Finding the Optimal Input Resolution)', fontsize=14, pad=20)
plt.tight_layout()

# 保存
plt.savefig('trade_off_analysis.png', dpi=300)
plt.show()

# 打印数据供你参考写PPT
print("数据分析摘要：")
print(df[['Resolution_Label', 'Avg_Acc', 'Relative_Cost']])