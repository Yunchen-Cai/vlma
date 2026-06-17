# ROI 混合验证实验（中文版）

## 1. 实验目标

本实验旨在回答一个核心问题：

> 在装配完成度验证任务中，VLM 的性能提升究竟来自真正的局部视觉特征学习，还是仅仅来自 prompt engineering 或输出偏置？

为此，我们围绕目标零件构建 ROI 对齐监督，并系统比较以下训练方式：

- `Full-only`
- `ROI-only`
- `Full+ROI mixed`

同时，我们进一步考察：

- ROI 监督能否扩展到多零件验证
- ROI 分支能否整合进统一多任务装配 VLM
- guided prompt 是否能替代 ROI 监督
- ROI 监督是否具备更强的数据效率

## 2. 方法概述

### 2.1 任务定义

本文将装配完成度验证建模为一个二分类视觉判别问题。给定一张当前工位图像和一个目标零件名称，模型需要判断该零件当前状态是：

- `Finish`
- `Unfinish`

为保证评测稳定且便于自动解析，模型输出统一约束为 JSON：

```json
{"part": "...", "verification": "Finish/Unfinish"}
```

### 2.2 ROI 对齐监督

全图输入保留了完整工位上下文，但完成度判断通常依赖于高度局部化的细粒度视觉线索，例如：

- 孔位是否同心
- 边缘间隙是否均匀
- 零件是否完全贴合
- 零件与配合面之间是否存在残余偏移

因此，本文围绕目标零件构建 ROI 裁剪图，并将其作为额外监督信号加入微调训练中。

在统一的 full-SFT 框架下，我们定义三种训练变体：

- `Full-only`：只使用全图
- `ROI-only`：只使用 ROI 图像
- `Full+ROI mixed`：同一源图像同时提供一个全图样本和一个 ROI 样本

所有模型均从相同的 `Qwen2.5-VL-7B-Instruct` 基座初始化，并采用 full supervised fine-tuning，而不是 LoRA，以避免参数高效微调策略对 ROI 结论造成混淆。

### 2.3 统一多任务扩展

为评估 ROI 监督能否被整合进通用装配 VLM，而不仅仅作用于单任务验证器，本文进一步将 cover ROI 完成度分支与 general assembly 数据合并训练，构建统一多任务模型。我们比较三种 ROI 混合强度：

- `Unified mixed`
- `Unified mixed x2`
- `Unified mixed x4`

其中 `x2` 和 `x4` 表示对 ROI 验证分支进行更强的过采样。

## 3. 实验设置

### 3.1 Cover 单零件验证

主实验目标零件为 `Port End Cover`。

数据来源：

- 训练：`2.3vlm_status_frames`
- 验证：`3.14vlm_verification_frames`
- 严格独立测试：`3.16test_vlm_verification_frames`

样本规模：

- `Full-only`: 212
- `ROI-only`: 212
- `Full+ROI mixed`: 424

评测规模：

- `3.14 full`: 218
- `3.14 roi`: 218
- `3.16 full`: 285
- `3.16 roi`: 285

### 3.2 四零件扩展验证

为排除“单一零件过拟合”的解释，本文构建四零件验证任务，覆盖：

- `Port End Cover`
- `Drive Gear`
- `House`
- `Thrust Block`

训练规模：

- `Full-only`: 519
- `ROI-only`: 519
- `Full+ROI mixed`: 1038

评测总规模：

- `all = 224`

### 3.3 统一多任务实验

通用装配训练集：

- `clean_assembly_sft_12.23merged.json`
- 1709 samples

通用测试集：

- `1.26.test.json`
- 545 samples

统一多任务训练集规模：

- `Unified mixed`: 2133
- `Unified mixed x2`: 2557
- `Unified mixed x4`: 3405

## 4. 主要实验结果

### 4.1 单零件主结果

在较容易的 `3.14` 验证集上，三种 ROI-aware 方案都接近饱和：

| 模型 | Accuracy |
| --- | ---: |
| Full-only | 99.54% |
| ROI-only | 99.54% |
| Full+ROI mixed | 100.00% |

因此，真正关键的证据来自更严格、独立的 `3.16` 测试集：

| 模型 | Accuracy | Precision | Recall | F1 | FPR |
| --- | ---: | ---: | ---: | ---: | ---: |
| Full-only | 92.11% | 0.8669 | 0.9929 | 0.9256 | 14.93% |
| ROI-only | 97.89% | 0.9891 | 0.9681 | 0.9785 | 1.04% |
| Full+ROI mixed | **99.30%** | **0.9929** | **0.9929** | **0.9929** | **0.69%** |

结论：

- ROI 监督显著降低了 `Unfinish -> Finish` 的误接受
- `Full+ROI mixed` 是当前单零件最强方案
- 提升并非来自简单输出偏置，而是来自局部视觉判别能力提升

### 4.2 四零件扩展结果

| 模型 | Accuracy | Precision | Recall | F1 | FPR | Unfinish Accuracy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Full-only | 60.65% | 0.6443 | 1.0000 | 0.7837 | 60.23% | 29.17% |
| ROI-only | 97.77% | 1.0000 | 0.9510 | 0.9749 | 0.00% | 100.00% |
| Full+ROI mixed | **100.00%** | **1.0000** | **1.0000** | **1.0000** | **0.00%** | **100.00%** |

结论：

- 四零件结果进一步证明 ROI 监督并非只对单一零件生效
- `Full-only` 在多零件场景下会出现严重误接受
- `Full+ROI mixed` 同时保留了上下文信息和最强的局部判别能力

### 4.3 Guided Prompt 对照实验

对 `Full+ROI mixed` 模型，我们还测试了 guided prompt：

| 指标 | 数值 |
| --- | ---: |
| Accuracy | 66.44% |
| Part Accuracy | 94.37% |
| Finish Accuracy | 87.92% |
| Unfinish Accuracy | 46.93% |
| FPR | 52.97% |

结论：

- guided prompt 可能对零件名识别和显式推理表达有帮助
- 但它不能替代 ROI 监督
- 尤其在 `Unfinish` 判别上非常不稳定，会严重拉高误接受

因此，当前最推荐的主方法仍然是：

```text
Full+ROI mixed + plain prompt
```

### 4.4 统一多任务主结果

| 模型 | General Joint Acc. | Cover 3.16 Acc. |
| --- | ---: | ---: |
| General-only | 59.08% | 47.54% |
| Unified mixed | **60.73%** | **99.30%** |
| Unified mixed x2 | 59.27% | 94.39% |
| Unified mixed x4 | 60.00% | 95.44% |

结论：

- 适度 ROI 混合可以同时保留 general 能力和强验证能力
- ROI 过采样过强反而破坏模型平衡
- `Unified mixed` 是统一模型中的最佳混合强度

### 4.5 ROI 提供器敏感性实验

对最佳 `Full+ROI mixed` 四零件检查点在两类受控扰动下重新评估:

| 扰动档 | Accuracy | FPR | Unfinish Acc. |
| --- | ---: | ---: | ---: |
| GT ROI | 100.00 % | 0.00 % | 100.00 % |
| 中心偏移 ± 5 % | 100.00 % | 0.00 % | 100.00 % |
| 中心偏移 ± 10 % | 95.54 % | 8.20 % | 91.80 % |
| 中心偏移 ± 15 % | 97.32 % | 3.28 % | 96.72 % |
| 尺度抖动 ± 10 % | 97.32 % | 4.92 % | 95.08 % |
| 尺度抖动 ± 20 % | 96.43 % | 6.56 % | 93.44 % |
| Full-only(无 ROI) | 60.65 % | 60.23 % | 29.17 % |

结论:

- 在 ± 5–± 15 % 中心偏移、± 10–± 20 % 尺度抖动整个区间内, 验证 Accuracy 始终远高于 Full-only 下界
- 最差 FPR (± 10 % 中心偏移下 8.20 %) 比 Full-only 基线 (60.23 %) 好近一个数量级
- 任何具备亚 10 % 中心 / 尺度误差的检测器均可胜任部署时的 ROI 提供器, 系统主张端到端闭环
- 该结果对应论文 §4.3.2 Table 7 与 Fig. 10

### 4.6 跨零件零样本诊断

将仅训练于 Port End Cover 的 `Full+ROI mixed` 检查点直接评估于四零件测试集:

| 零件 | GT Finish 预测 Finish | GT Finish 预测 Unfinish | GT Unfinish 预测 Unfinish | GT Unfinish 预测 Finish |
| --- | ---: | ---: | ---: | ---: |
| Port End Cover(同分布) | 13 | 0 | 18 | 0 |
| Drive Gear(未见) | 0 | 13 | 16 | 0 |
| Gear Housing(未见) | 0 | 15 | 14 | 0 |
| Thrust Block(未见) | 0 | 10 | 13 | 0 |
| 合计 | 13 / 51 | 38 / 51 | 61 / 61 | 0 / 61 |

结论:

- 零件名识别仍为完美 (224 / 224 帧)
- 同分布 Cover 切片仍完美 (31 / 31)
- 三种未见零件上, 所有 Finish 帧都被预测为 Unfinish: 完成度验证不能在本监督方案下零样本迁移
- 表面 0 % 聚合 FPR 反映退化的"默认 Unfinish"响应, 不能解读为保守安全
- 新产品变体的 SOP 上线必须为每个新零件提供少量完成度标签
- 该结果对应论文 §5.2(iv) 与附录 C Table C.1

## 5. Ablation 与误差分析

### 5.1 Prompt engineering 不能替代 ROI supervision

guided prompt 的结果说明：

- 它可能帮助模型“说得更像在分析”
- 也可能提高零件名识别
- 但它不能稳定地提高完成度验证表现
- 对于安全敏感的 `Unfinish` 样本，反而容易出现误接受

因此，ROI-aligned supervision 才是当前性能提升的主要来源。

### 5.2 ROI 过采样比例消融

统一多任务实验表明存在明显 sweet spot：

- `Unified mixed` 最优
- `x2` 与 `x4` 都会降低 cover 验证性能

这说明 ROI 分支最有效的注入方式不是主导整个训练分布，而是作为平衡的辅助监督信号。

### 5.3 General 任务分解分析

`Unified mixed` 相比 `General-only`：

| 指标 | General-only | Unified mixed |
| --- | ---: | ---: |
| Action Acc. | 92.48% | 94.86% |
| Tool Acc. | 96.70% | 96.88% |
| Part Acc. | 93.39% | 95.23% |
| Phase Acc. | 65.14% | 64.22% |
| Joint Acc. | 59.08% | 60.73% |

更关键的是：

- 若只要求 `action + tool + part` 同时正确
- `General-only`: 90.09%
- `Unified mixed`: 92.29%

说明：

- ROI 分支已经明显改善了动作、工具、零件识别
- 当前 general joint 提升有限的主因不是局部视觉，而是 `phase` 歧义

### 5.4 Phase 混淆分析

当前 `phase` 的主要混淆是：

- `start -> mid`
- `finish -> mid`
- `mid -> finish`
- `mid -> start`

并且：

- `General-only` 中 75.8% 的 joint failure 是“只有 phase 错”
- `Unified mixed` 中 80.4% 的 joint failure 也是“只有 phase 错”

这说明：

- 单帧 general benchmark 的主瓶颈是时序边界模糊
- 这与后续引入 SOP/FSM 的动机高度一致

## 6. Few-shot 结果

当前 few-shot 已完成：

- `Full-only`
- `ROI-only`
- 训练规模：`50 / 100 / 200 / 300 / 400`

ROI-test 结果摘要：

| 模型 | 50 | 100 | 200 | 300 | 400 |
| --- | ---: | ---: | ---: | ---: | ---: |
| Full-only Accuracy | 93.52% | 59.26% | 97.22% | 92.59% | 96.30% |
| ROI-only Accuracy | 95.37% | 95.37% | 97.22% | 100.00% | 100.00% |

主要结论：

- ROI-only 在 ROI 视角上展现出更强的数据效率
- 50-shot 时 ROI-only 已优于 Full-only
- 300/400-shot 时 ROI-only 在 ROI-test 上达到 100%

当前限制：

- 还缺 `Full+ROI mixed` 的完整 few-shot 曲线
- 还缺多随机种子重复

因此 few-shot 目前更适合作为辅助证据，而不是唯一主结果。

## 7. 当前最推荐的方法

基于现有所有实验，当前最推荐的最终方案是：

```text
Qwen2.5-VL-7B-Instruct
+ Full SFT
+ Full+ROI mixed training
+ plain prompt inference
```

原因：

- cover 单零件最优
- 四零件最优
- 能平衡局部判别与全局上下文
- 不像 guided prompt 那样显著扰乱 `Unfinish` 判别

## 8. 对论文写作的建议

最推荐的论文主线是：

1. ROI supervision 显著提升单零件完成度验证
2. 四零件扩展进一步排除单零件过拟合解释
3. guided prompt 不能替代 ROI supervision
4. ROI 分支可在合理比例下整合到统一多任务 VLM
5. general task 的主要剩余瓶颈是 `phase` 歧义，因此后续需要 SOP/FSM

在投稿时：

- 主结果应强调 `Full+ROI mixed + plain prompt`
- guided prompt 应作为对照或负结果分析写入 ablation
- few-shot 可作为辅助证据展示 ROI 监督的数据效率优势

