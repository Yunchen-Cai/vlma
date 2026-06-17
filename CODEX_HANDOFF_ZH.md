# Codex 交接文档（中文版）

## 1. 文档用途

本文档用于向下一位接手本项目的 Codex 实例或研究成员说明当前仓库状态、已完成实验、关键结论、剩余工作与推荐实验路线。重点覆盖：

- 仓库主要组成
- 当前论文主线与研究目标
- 已完成的数据准备、训练、评测与可视化
- 已验证的主结果
- 后续最值得继续推进的实验方向

本项目当前核心主题是：**基于 ROI 对齐监督的装配完成度验证，以及其与统一多任务 VLM 的结合方式。**

## 2. 仓库概览

仓库主要包含三个部分：

### 2.1 Python VLM 实验管线

用途：

- 数据集构建
- VLM 全参数微调
- 完成度验证评测
- ROI 实验、多任务实验、few-shot 实验

关键目录：

- `python/src/`
- `python/data/`
- `python/output/`
- `python/ROI_MIXED_EXPERIMENT.md`
- `python/ROI_MIXED_EXPERIMENT_ZH.md`

### 2.2 Java 后端

目录：

- `VideoAssemblyMonitor/`

用途：

- 装配监控服务
- 流程状态机 / 后端接口

说明：

- 与本轮 ROI 论文实验主线无直接耦合
- 本轮未作为主要修改对象

### 2.3 前端

目录：

- `VideoAssemblyMonitorWeb/`

用途：

- 监控可视化界面

说明：

- 本轮未作为主要修改对象

## 3. 当前论文主线

当前最清晰、最适合投稿的论文主线是：

1. 证明 ROI 对齐监督可以增强 VLM 对局部完成度特征的感知能力。
2. 证明该收益并非来自 prompt engineering，而是真正来自视觉监督。
3. 证明 ROI 监督不仅能在单零件任务中有效，也能扩展到多零件验证。
4. 证明 ROI 分支还能以合理比例整合进统一多任务装配 VLM。
5. 进一步说明：统一模型在 general task 上的主要瓶颈不是局部视觉，而是单帧 phase 判别的时序歧义，这为后续引入 SOP/FSM 提供动机。

当前最推荐的最终方法是：

```text
Qwen2.5-VL-7B-Instruct
+ Full SFT
+ Full+ROI mixed training
+ plain verification prompt
```

## 4. 已完成的数据与实验工作

### 4.1 Cover 单零件 ROI 验证数据

当前 cover 主实验采用以下数据线：

- 训练源：`2.3vlm_status_frames`
- 验证源：`3.14vlm_verification_frames`
- 严格独立测试源：`3.16test_vlm_verification_frames`

对应构建出的实验数据目录：

- `python/data/roi_experiment_cover_train_2p3/`
- `python/data/roi_experiment_cover_val_314/`
- `python/data/roi_experiment_cover_test_316/`

训练集规模：

- `Full-only`: 212
- `ROI-only`: 212
- `Full+ROI mixed`: 424

评测集规模：

- `3.14 full`: 218
- `3.14 roi`: 218
- `3.16 full`: 285
- `3.16 roi`: 285

### 4.2 四零件 ROI 验证数据

四零件任务覆盖：

- `Port End Cover`
- `Drive Gear`
- `House`
- `Thrust Block`

对应目录：

- `python/data/roi_experiment_v2_4part/`

训练集规模：

- `Full-only`: 519
- `ROI-only`: 519
- `Full+ROI mixed`: 1038

评测总规模：

- `all = 224`

### 4.3 统一多任务数据

通用装配训练集：

- `python/data/clean_assembly_sft_12.23merged.json`
- 样本数：1709

通用测试集：

- `python/data/1.26.test.json`
- 样本数：545

统一多任务训练集：

- `general_plus_coverx_mixed_sft_v1.json`: 2133
- `general_plus_coverx_mixed_x2_sft_v1.json`: 2557
- `general_plus_coverx_mixed_x4_sft_v1.json`: 3405

## 5. 已完成的训练与评测结果

### 5.1 Cover 单零件主结果

严格独立 `3.16` 测试集：

| 模型 | Accuracy | F1 | FPR |
| --- | ---: | ---: | ---: |
| Full-only | 92.11% | 0.9256 | 14.93% |
| ROI-only | 97.89% | 0.9785 | 1.04% |
| Full+ROI mixed | 99.30% | 0.9929 | 0.69% |

结论：

- ROI 监督显著降低了 `Unfinish -> Finish` 的误接受
- 当前单零件主线最推荐方法是 `Full+ROI mixed`

### 5.2 四零件主结果

| 模型 | Accuracy | F1 | FPR | Unfinish Accuracy |
| --- | ---: | ---: | ---: | ---: |
| Full-only | 60.65% | 0.7837 | 60.23% | 29.17% |
| ROI-only | 97.77% | 0.9749 | 0.00% | 100.00% |
| Full+ROI mixed | 100.00% | 1.0000 | 0.00% | 100.00% |

结论：

- 四零件结果极强地支持 ROI 的必要性
- `Full-only` 在多零件细粒度完成度任务上会严重误接受
- `Full+ROI mixed` 是四零件最优方案

### 5.3 Guided Prompt 实验

结果目录：

- `python/output/eval/coverx_full_roi_mixed_eval_316_guided_long/`

主要结果：

- `accuracy = 66.44%`
- `part_accuracy = 94.37%`
- `finish_accuracy = 87.92%`
- `unfinish_accuracy = 46.93%`
- `FPR = 52.97%`

解释：

- guided prompt 可能对零件名识别和显式推理表达有帮助
- 但对完成度验证尤其是 `Unfinish` 判别非常不稳定
- 当前证据不支持将 guided prompt 作为主方法

### 5.4 统一多任务主结果

| 模型 | General Joint Acc. | Cover 3.16 Acc. |
| --- | ---: | ---: |
| General-only | 59.08% | 47.54% |
| Unified mixed | 60.73% | 99.30% |
| Unified mixed x2 | 59.27% | 94.39% |
| Unified mixed x4 | 60.00% | 95.44% |

结论：

- 合理比例的 ROI 混合可以同时保留 general 能力并获得强验证能力
- ROI 过采样过强会破坏统一模型平衡
- `Unified mixed` 是统一模型中的最佳混合点

### 5.5 General Task 分解分析

`Unified mixed` 相比 `General-only`：

- `action`: 92.48% -> 94.86%
- `tool`: 96.70% -> 96.88%
- `part`: 93.39% -> 95.23%
- `phase`: 65.14% -> 64.22%
- `joint`: 59.08% -> 60.73%

更重要的是：

- 若不计入 `phase`，只要求 `action + tool + part` 同时正确
- `General-only`: 90.09%
- `Unified mixed`: 92.29%

说明：

- ROI 分支确实提升了动作、工具、零件识别
- general joint 提升幅度不大的主要原因是 `phase` 任务本身是单帧时序歧义瓶颈

主要 phase 混淆：

- `start -> mid`
- `finish -> mid`
- `mid -> finish`
- `mid -> start`

### 5.6 Few-shot 实验

已完成：

- `Full-only`
- `ROI-only`
- 训练样本规模：`50 / 100 / 200 / 300 / 400`

主要结果文件：

- `python/output/fewshot_roi_test_table.csv`
- `python/output/fig_fewshot_curves.csv`
- `python/output/fig_fewshot_curves.png`

主要结论：

- ROI-only 在 ROI-crop 测试视角上展现出更好的数据效率
- 50-shot 时 ROI-only 已优于 Full-only
- 300/400-shot 时 ROI-only 在 ROI-test 上达到 100%

当前不足：

- 还缺 `Full+ROI mixed` 的完整 few-shot 曲线
- 还缺多随机种子重复

因此：

- few-shot 可以作为论文中的辅助证据
- 但不宜在当前阶段作为绝对主图主表

### 5.7 ROI 扰动敏感性实验

已完成:

- 基于四零件留出测试集,对 GT ROI 应用两类受控扰动:
  - 中心偏移 `c5 / c10 / c15`(±5 / ±10 / ±15 % 边长)
  - 尺度抖动 `s10 / s20`(±10 / ±20 %)
- 在每一档扰动上重新评估 `Full+ROI mixed` 检查点的验证 Accuracy 与 FPR

主要结果文件:

- `python/data/roi_experiment_v2_4part/eval_perturb/test_roi_perturb_<tag>_v1.json`
- `python/output/<MODEL_NAME>/.../roi_sensitivity_summary.csv`

主要结论:

- 在 ± 5–± 15 % 中心偏移与 ± 10–± 20 % 尺度抖动整个区间内, 验证 Accuracy 始终远高于 Full-only 下界(60.65 %)
- 所观察到的最差 FPR 仅为 8.20 %, 比 Full-only 基线(60.23 %)好一个数量级
- 论文据此论证: 任何具备亚 10 % 中心 / 尺度误差的检测器(或固定相机查找表)均可胜任部署时的 ROI 提供器
- 直接对应论文 §4.3.2 Table 7 与 Fig. 10

复现命令:

```bash
cd /mnt/workspace/users/caiyunchen/vlma
bash python/src/run_roi_sensitivity_eval.sh
```

扰动通过逐样本确定性 RNG 采样(以图像 basename 为种子), 重跑可得二进制一致的结果。

### 5.8 跨零件零样本诊断

已完成:

- 将仅训练于 Port End Cover 的 `Full+ROI mixed` 检查点直接评估于四零件留出测试集
- 不接触主齿轮 / 齿轮壳 / 轴瓦块的任何训练样本

主要结果:

- 零件名识别仍为完美 (224 / 224 帧)
- 同分布的 Port End Cover 切片仍完美 (31 / 31 帧,13 Finish + 18 Unfinish 全部正确)
- 三种未见零件上 0 / 38 个 Finish 帧被正确预测(全部被预测为 Unfinish)
- 聚合 Finish 召回率因此降至 25.49 %
- 表面 FPR = 0 % 并非保守安全, 而是退化的"默认 Unfinish"响应

主要结论:

- 完成度验证不能在本监督方案下零样本迁移到新零件
- 新产品变体的 SOP 上线必须为每个新零件提供少量完成度标签
- 直接对应论文 §5.2(iv) 与附录 C Table C.1

复现命令:

```bash
cd /mnt/workspace/users/caiyunchen/vlma
TRANSFORMERS_NO_TF=1 USE_TF=0 CUDA_VISIBLE_DEVICES=0 \
VLM_MODEL_ID=/mnt/workspace/users/caiyunchen/vlma/python/output/coverx_full_roi_mixed_fullsft_v2 \
VLM_EVAL_EXPERIMENT_NAME=coverx_full_roi_mixed_on_fourpart_zero_shot \
VLM_EVAL_FILES=/mnt/workspace/users/caiyunchen/vlma/python/data/roi_experiment_v2_4part/eval/test_full_v1.json,/mnt/workspace/users/caiyunchen/vlma/python/data/roi_experiment_v2_4part/eval/test_roi_v1.json \
python python/src/evaluate_model.py
```

## 6. 当前推荐的论文叙事

最推荐的论文叙事结构是：

1. 单零件独立测试集上，ROI supervision 显著降低 false acceptance。
2. 四零件实验进一步说明 ROI 效果不是单零件记忆。
3. guided prompt 不能替代 ROI supervision。
4. 统一多任务实验说明 ROI 分支可以合理整合进 general VLM。
5. general task 的主要剩余瓶颈是 phase 歧义，这为后续 SOP/FSM 提供自然动机。

## 7. 当前最推荐的方法配置

```text
Base model:
  Qwen2.5-VL-7B-Instruct

Training:
  full supervised fine-tuning

Verification data:
  Full+ROI mixed

Inference prompt:
  plain prompt
```

不推荐作为主方法的方案：

- `guided prompt` 直接用于最终完成度判断
- `Unified mixed x2 / x4` 作为统一模型主配置
- 仅用 `Full-only` 做多零件完成度验证

## 8. 后续最值得继续做的工作

优先级建议：

1. 补齐 `Full+ROI mixed` 的 few-shot 曲线与多 seed 重复
2. 输出四零件按零件拆分的结果表
3. 为论文生成正式图：
   - cover 主结果柱状图
   - four-part 三组对比图
   - few-shot 曲线图
   - general phase confusion matrix
4. 在后续工作中引入 SOP/FSM，专门解决 phase 歧义

## 9. 关键结果文件索引

单零件：

- `python/output/eval/coverx_full_only_eval_316_plain/metrics_summary.csv`
- `python/output/eval/coverx_roi_only_eval_316_plain/metrics_summary.csv`
- `python/output/eval/coverx_full_roi_mixed_eval_316_plain/metrics_summary.csv`

guided prompt：

- `python/output/eval/coverx_full_roi_mixed_eval_316_guided_long/metrics_summary.csv`

四零件：

- `python/output/eval/fourpart_full_only_fullsft_v2_eval/metrics_summary.csv`
- `python/output/eval/fourpart_roi_only_fullsft_v2_rerun_eval_fourpart/metrics_summary.csv`
- `python/output/eval/fourpart_full_roi_mixed_fullsft_v2_rerun_eval_fourpart/metrics_summary.csv`

统一多任务：

- `python/output/eval/general_1223_eval_126_general/summary.csv`
- `python/output/eval/multitask_general_coverx_mixed_eval_126_general/summary.csv`
- `python/output/eval/multitask_general_coverx_mixed_x2_eval_126_general/summary.csv`
- `python/output/eval/multitask_general_coverx_mixed_x4_eval_126_general/summary.csv`

few-shot：

- `python/output/fewshot_roi_test_table.csv`
- `python/output/fig_fewshot_curves.csv`
- `python/output/fig_fewshot_curves.png`

