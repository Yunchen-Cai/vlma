# 论文补强实验操作交接文档(给后续 agent)

**任务编号:** OPS-001
**任务目标:** 在 VLMA 论文(`/Users/caiyunchen.3/vlma_paper_draft_v1_en.docx`)中补全 5 项制造领域 SCI Q1 必备的系统级实证内容:**A3 (FSM 端到端)、B2 (latency)、B4 (timeline 可视化)、A5 (alarm threshold 说明)、A6 (VLM confidence calibration)**。

**预期工作量:** 一个有 SSH + Python + 论文写作经验的 agent,顺利情况下 **5–7 天**。

**完成标准:**
- 论文新增 §4.5 "End-to-end alarm-level evaluation",含 1 个新表(Table 10)+ 1 个新图(Fig. 12 timeline)
- 论文 §3.5 alarm threshold 段补来源说明
- 论文 §5.1 加 VLM 延迟数字(ms/frame、VRAM、throughput)
- 论文新增 Fig. 13 reliability diagram + Appendix D calibration analysis
- 所有数字基于真实实验,**禁止任何捏造数据**(详见 §0 红线)

---

## 0. 红线和工作纪律

在动手之前必读。**任何违反以下红线的行为都视为不合格交付。**

### 0.1 数据真实性

- **所有数字必须来自真实实验运行,严禁估算 / 估测 / 复用其他实验数据冒充新实验。**
- 跑实验时把原始输出文件(JSON / CSV / log)留在云端 `/mnt/workspace/users/caiyunchen/vlma/python/output/eval/` 子目录下,文件名带日期戳,**至少保留 30 天**。
- 论文 docx 里每个新数字都要在脚本里能 trace 回原始 output 文件。
- 如果某个实验跑出来的数字反直觉(比如 alarm precision 反而低于 baseline),**不要修改数字,先写解释**。reviewer 看到反直觉但被认真解释的结果,比看到完美但说不通的结果更信任。

### 0.2 改 docx 的纪律(从 9 轮血泪史里学到的)

详见 `/Users/caiyunchen.3/vlma/PAPER_HANDOFF.md` §8 "Hard rules"。这里只重述最容易踩的:

1. **任何改动前**先 `cp` 一份带日期戳的备份:`cp .../vlma_paper_draft_v1_en.docx .../vlma_paper_draft_v1_en_BACKUP_before_<your-task-tag>_$(date +%Y%m%d).docx`
2. **不要重渲染 docx**,只用 `python-docx` 做局部 edit
3. **不要破坏已有的 cross-reference**(`_Sec_*` / `_Fig_*` / `_Tab_*` / `_Ref_*` bookmark 和 hyperlink)
4. **不要重新排版表格** — 用 `deepcopy` 现有 Table 7 / Table 8 的 XML 元素作为新表模板
5. **每次编辑结束后跑** `python3 /tmp/audit_en.py`(audit 脚本,见 §6),要求 0 errors

### 0.3 跟用户沟通的频率

- **每完成一个子任务**(A3 / B2 / B4 / A5 / A6 各算一个)报告一次进度
- **任何反直觉数据**(比如 alarm precision 低于 80%)在动笔回填论文前,先把数字摆出来给用户看
- **任何对实验设计的修改**(比如想换一组 sequence)先问用户

---

## 1. 现有资产清单(动手前都要确认存在)

### 1.1 论文相关

| 文件 | 用途 |
|---|---|
| `/Users/caiyunchen.3/vlma_paper_draft_v1_en.docx` | 英文论文权威版,要编辑的就是它 |
| `/Users/caiyunchen.3/vlma_paper_draft_v1_zh.docx` | 中文版,本任务**暂不同步**(本任务完成后再考虑) |
| `/Users/caiyunchen.3/vlma_paper_draft_v1.md` | markdown 版,本任务**暂不同步** |
| `/Users/caiyunchen.3/vlma/PAPER_HANDOFF.md` | 论文写作的总纲 |
| `/Users/caiyunchen.3/vlma/PAPER_REVIEW_ZH.md` | 上一轮 review 文档 |

### 1.2 云端服务器

| 项 | 值 |
|---|---|
| Host | `116.198.70.4` |
| Port | `32551` |
| User | `root` |
| Password(已硬编码) | 见 `/Users/caiyunchen.3/vlma/CODEX_HANDOFF.md` 或问用户 |
| 项目路径 | `/mnt/workspace/users/caiyunchen/vlma` |
| Python | `/mnt/workspace/envs/conda3/envs/starVLA_chidafeng/bin/python` (transformers 4.57.3) |
| GPU | H200 ×8;评估用 `CUDA_VISIBLE_DEVICES=0` 即可 |

**云端无法访问 GitHub / HuggingFace(端口 443 timeout)。**任何依赖外网下载的模型 / 包,先从本地 Mac 下,再用 `rsync` 上传。

### 1.3 实验可复用资产

| 路径 | 说明 |
|---|---|
| `python/output/fourpart_full_roi_mixed_fullsft_v2_rerun/` | **A3 / B2 用的 checkpoint**(Full + ROI mixed,四零件) |
| `python/data/2.3vlm_status_frames/` | 标准 + 异常执行**视频帧目录**(文件名编码 sequence 信息) |
| `python/data/3.14vlm_verification_frames/` | 同上,3.14 录制 batch |
| `python/data/3.16test_vlm_verification_frames/` | 同上,3.16 录制 batch(holdout 用的) |
| `python/data/roi_experiment_v2_4part/metadata/split_test_v1.csv` | 4-part 测试集 ground truth |
| `python/src/evaluate_model.py` | VLM 逐帧 inference 脚本 |
| `python/src/compute_verification_metrics.py` | 已有的 metrics 聚合(用法见 `run_grounding_dino_eval.sh`) |
| `python/src/run_grounding_dino_roi.py` | Grounding DINO 推理脚本 |
| `python/src/run_grounding_dino_eval.sh` | 端到端 pipeline,可作为 shell 模板 |
| `python/src/run_roi_sensitivity_eval.sh` | 同上 |

### 1.4 文件名 → sequence 信息的规则(关键)

云端帧文件名格式有两种,**都自带 sequence 元信息**:

**格式 A(`2.3vlm_status_frames/`)**:
```
{状态}_{零件}_{子类}_f{帧号}.jpg
例:
  Correct_cover_correct_f110.jpg   → 正常 / 端盖 / 正确 / 第 110 帧
  Error_drive_gear_error_f1078.jpg  → 异常 / 主齿轮 / 错误 / 第 1078 帧
  Error_thrust_error_f55.jpg        → 异常 / 轴瓦块 / 错误 / 第 55 帧
```

**格式 B(`3.16test_vlm_verification_frames/`)**:
```
{产品执行编号} (N)_f{帧号}.jpg
例:
  cover_correct (1)_f0.jpg          → 端盖 / 正确执行 / 第 1 次录制 / 第 0 帧
  cover_correct (1)_f1001.jpg       → 同上 / 第 1001 帧
```

**A3 实验依赖这个命名规则**做 sequence 切分。如果实际文件名跟这里描述的不一致,**先 ssh 上去看一眼,如果有偏差给用户报告再决定**。

---

## 2. 任务 A3 — FSM 端到端实证(主菜)

**这是 5 项任务中最重要的一项,占总工作量 60%。**

### 2.1 实验设计

#### 2.1.1 实验目标

证明**完整流水线**(VLM perception → SOP-guided FSM → operator-facing alarm)在视频序列级别真的能工作。报告 3 类 alarm 的 precision / recall。

#### 2.1.2 数据构造

从 `2.3vlm_status_frames/` + `3.14vlm_verification_frames/` 中**构造 20 段 sequence**:
- **10 段 standard execution**(无错误,完整 SOP 走完),从 `Correct_*` 文件构造
- **10 段 abnormal execution**(故意触发以下三类错之一):
  - **4 段 ordering-violation**:乱序(例如 place port end cover 在 place gear housing 之前)
  - **3 段 timing-violation**:某步停留太久(超 τᵢ 上界)
  - **3 段 unfinished-completion**:某步表面完成但实际未就位(从 `Error_*_error_*` 文件构造)

**每段 sequence 长度:** ~30–60 帧(覆盖 SOP 中的 5–8 步)。

**总 sequence 帧数:** ~20 × 45 ≈ 900 帧。

#### 2.1.3 GT 标注

每段 sequence 需要标注:
- **predicted_sop_steps**:实际包含哪些 SOP 步骤(顺序)
- **expected_alarms**:理论上应该触发哪些 alarm,每个 alarm 标:
  - 类型(`ordering` / `timing` / `unfinished`)
  - 触发位置(从第几帧起应该触发)
- **standard execution 的 expected_alarms 应全部为空**

GT 标注表的样例(YAML / CSV 都可,推荐 JSON):

```json
{
  "sequence_id": "seq_abnormal_01",
  "frame_paths": [
    "2.3vlm_status_frames/Correct_cover_correct_f110.jpg",
    "2.3vlm_status_frames/Correct_cover_correct_f121.jpg",
    ...
  ],
  "expected_sop_path": ["place_mounting_flange", "place_gear_housing", ...],
  "expected_alarms": [
    {"type": "ordering", "first_frame_idx": 23, "node": "place_port_end_cover"},
    {"type": "unfinished", "first_frame_idx": 41, "node": "tighten_capscrew_3"}
  ]
}
```

#### 2.1.4 实验脚本架构

新建 3 个脚本:

1. `python/src/build_sequence_dataset.py` — 从已有帧文件 + 已有 SOP 知识构造 20 段 sequence 的 GT 标注 JSON
2. `python/src/fsm_state_machine.py` — Python 实现的 SOP-guided FSM(读 `python/data/sop_graph_gearpump.json`,消费 VLM prediction stream,输出每帧的 (Cᵢ(t), Eᵢ(t), Dᵢ(t), alarms_raised))
3. `python/src/run_fsm_end_to_end.py` — 把 sequence 喂给 VLM → 收集 prediction → 喂给 FSM → 比对 expected_alarms → 输出 alarm precision / recall

#### 2.1.5 Metrics 定义

按 alarm 类型分别计算:

**Per-alarm-type precision** = TP / (TP + FP),其中:
- TP = sequence 里 expected_alarms 触发了 ∧ FSM 实际触发了 ∧ 类型对 ∧ 触发帧偏差 ≤ 5 帧
- FP = FSM 触发了但 expected_alarms 没有

**Per-alarm-type recall** = TP / (TP + FN),其中:
- FN = expected_alarms 标了但 FSM 没触发

**总 precision / recall** = 三类 alarm 的 micro-average。

**False alarm rate on standard executions** = 10 段 standard execution 中触发了多少 alarm(理想是 0)。

#### 2.1.6 输出 deliverables

跑完实验后,云端应有:
- `python/output/eval/fsm_end_to_end_v1/sequence_results.csv`(每段 sequence 的 per-frame FSM state + alarms triggered)
- `python/output/eval/fsm_end_to_end_v1/per_alarm_metrics.csv`(三类 alarm 的 P/R + overall + false-alarm rate)
- `python/output/eval/fsm_end_to_end_v1/alarm_timing_distribution.json`(每个 expected alarm 的触发延迟,用于 §4.5 报告 alarm latency)

**这三个文件 rsync 回本地 Mac 后,论文回填才有依据。**

### 2.2 实施步骤

#### Step A3-1:构造 SOP graph JSON(0.5 天)

在云端 `/mnt/workspace/users/caiyunchen/vlma/python/data/sop_graph_gearpump.json` 新建。结构示例:

```json
{
  "nodes": [
    {
      "id": "place_mounting_flange",
      "actions_whitelist": ["place-mountingFlange"],
      "parents": [],
      "tau_lower_sec": 2.0,
      "tau_upper_sec": 8.0,
      "v_gated": true,
      "part": "Mounting Flange"
    },
    {
      "id": "place_gear_housing",
      "actions_whitelist": ["place-gearHousing"],
      "parents": ["place_mounting_flange"],
      "tau_lower_sec": 2.0,
      "tau_upper_sec": 8.0,
      "v_gated": true,
      "part": "Gear Housing"
    },
    ...
  ]
}
```

15 个节点,跟论文 §3.5 Fig. 7 描述一致(place_mounting_flange → place_gear_housing → place_drive_gear → place_driven_gear → install_thrust_block → place_port_end_cover → insert_capscrew_{1..4} → tighten_capscrew_{1..4} → final_verification_gate)。

τ 上下界先用 (2, 8) 秒(可调,但要在 Step A3-3 alarm threshold 调参时一起确认)。

`v_gated` 跟论文 §3.5 一致:gear-insertion / capscrew-insertion 节点 `false`,其余 `true`。

#### Step A3-2:实现 FSM(2 天)

`python/src/fsm_state_machine.py`,关键 API:

```python
class SOPGuidedFSM:
    def __init__(self, sop_graph_json_path: str,
                 ordering_threshold: float = 0.05,
                 timing_threshold: float = 0.05,
                 verification_threshold: float = 0.5):
        ...

    def consume_observation(self, t: float, vlm_output: dict, confidence: float):
        """
        vlm_output:
          either {"action": ..., "tool": ..., "part": ...}  (General mode)
          or     {"part": ..., "verification": ...}         (Verification mode)
        confidence: ρₜ ∈ [0, 1]
        """
        # 1. Match vlm_output to candidate nodes via whitelist
        # 2. Distribute confidence-weighted probability across matches
        # 3. Propagate backward by parent readiness F_i (Eq. 4)
        # 4. Update C_i(t), F_i(t), E_i(t), D_i(t)
        # 5. Check alarm conditions; if E_i > 0.05 or D_i > 0.05 or
        #    unverified-completion-after-action, raise alarm.
        ...
        return {"alarms": [...], "state": {...}}

    def get_state_snapshot(self):
        """For per-frame logging into sequence_results.csv."""
        ...
```

实现要点:
- 完全照 §3.5 论文文字的描述实现,**不要做新的设计**
- Eq. (4) 父就绪度 Fᵢ = ∏ⱼ∈πᵢ Cⱼ,跟论文公式严格一致
- 三类 alarm:
  - Ordering: 当某个节点的 Eᵢ = Cᵢ · (1 - Fᵢ) > 0.05 时触发
  - Timing: 当某个节点的 visit probability > τᵢ 上界,Dᵢ 累积 > 0.05 时触发
  - Unfinished completion: V-gated 节点 Cᵢ > 0.7 但没有 Verification mode 的 Finish 确认

输出 sample test 文件 `python/src/test_fsm.py`:5 帧的 toy stream 跑通,断言三类 alarm 都能触发。**这一步不通过不进 Step A3-3。**

#### Step A3-3:构造 20 段 sequence GT(1 天)

写 `python/src/build_sequence_dataset.py`:

```python
"""
Build 20 sequences from 2.3vlm_status_frames + 3.14vlm_verification_frames.

10 standard executions: from Correct_* files of multiple parts
10 abnormal executions: from Error_*_error_* files

Each sequence covers 5-8 SOP steps, ~30-60 frames.
Output: python/data/fsm_eval_sequences_v1.json
"""
```

具体怎么选 sequence,**人工指定一个 sequence map**(在脚本里 hardcode),不要让脚本自动 random select(否则不可复现)。

序列构造完后,跑:
```bash
python3 python/src/build_sequence_dataset.py
# Sanity check
python3 -c "
import json
d = json.load(open('python/data/fsm_eval_sequences_v1.json'))
for seq in d:
    print(f\"{seq['sequence_id']}: {len(seq['frame_paths'])} frames, {len(seq.get('expected_alarms', []))} alarms\")
"
```

#### Step A3-4:写主实验 driver(1 天)

`python/src/run_fsm_end_to_end.py`:

```python
"""
For each sequence:
  1. Load frames in order
  2. For each frame: call evaluate_model.py-style VLM inference
     (Full + ROI mixed checkpoint, in General mode for non-V-gated nodes,
      Verification mode for V-gated nodes with GT-ROI input)
  3. Feed each (vlm_output, confidence, timestamp) to FSM
  4. Collect per-frame FSM state + alarms_raised
  5. Compare to expected_alarms in GT
  6. Compute per-alarm-type precision, recall, latency
Output: python/output/eval/fsm_end_to_end_v1/...
"""
```

**关键细节:**
- ROI crops 用 GT bounding boxes(`metadata/split_test_v1.csv`),不要用 Grounding DINO — 这样 FSM 评估独立于 detector
- Mode alternation:V-gated 节点 → Verification mode;G-only 节点 → General mode
- VLM checkpoint:`python/output/fourpart_full_roi_mixed_fullsft_v2_rerun`

写一个 shell launcher `python/src/run_fsm_end_to_end_eval.sh` 类似 `run_grounding_dino_eval.sh` 的结构。

#### Step A3-5:跑实验 + 收集结果(1 天 + GPU 等待)

预计 20 段 sequence × 平均 45 帧 × 0.5 秒/帧(VLM 推理) = 7.5 分钟。FSM consume 是毫秒级。**总计 ~10 分钟跑完。**

跑完后:
1. ssh 上去 cat `per_alarm_metrics.csv` 看数字
2. 如果数字怪(precision < 50% 或 recall < 50%),**先报告给用户**,不要直接写论文
3. 如果数字合理(precision > 70%, recall > 70%),进 Step A3-6

#### Step A3-6:写 §4.5 + Table 10 + 回填(1 天)

在 docx 里**新建 §4.5 H2 section**(在 §4.4 之后):

```
4.5 End-to-end alarm-level evaluation
```

内容三段(参考下面 §4 的文字框架),然后插一个 Table 10。

### 2.3 §4.5 文字框架(等数字填回)

把这段直接当作 docx 内容的草稿:

---

**4.5 End-to-end alarm-level evaluation**

(段 1 — Motivation)

> While Sections 4.2–4.4 isolate the VLM contribution by reporting frame-level verification metrics, the proposed framework's system-level claim rests on the end-to-end behaviour of the closed loop: the VLM's per-frame predictions feed into the SOP-guided state machine of Section 3.5, which is responsible for surfacing operator-facing alarms. This section therefore evaluates the deployed pipeline at the alarm level, using sequence-level inputs that mirror the temporal structure of a real shop-floor monitoring stream.

(段 2 — Experimental setup)

> Twenty manually-curated execution sequences are constructed from the source recordings of Section 4.1: ten standard executions in which the operator follows the full SOP without interruption, and ten abnormal executions that each carry one of three error modalities — four ordering violations (a step performed before its dependencies are complete), three timing violations (a step that exceeds the upper bound of its timing budget τᵢ), and three unfinished-completion errors (a step that visually approximates completion but fails the Verification gate). Each sequence spans @@AVG_FRAMES@@ frames on average, covering five to eight SOP steps. For each sequence, the ground-truth annotation specifies the expected SOP step path and, for abnormal executions, the type, originating node, and earliest frame index at which the alarm should be raised. Per-frame predictions are obtained from the same Full + ROI mixed checkpoint used in Section 4.2.2, with General-mode and Verification-mode invocations scheduled by the G / V partition of Section 3.5. The detected alarms are then aligned against ground-truth alarms with a tolerance of five frames on the trigger position; a detected alarm whose type and node match the ground truth within this window is counted as a true positive, all other detections as false positives, and missed ground-truth alarms as false negatives.

(段 3 — Results)

> Table 10 reports the resulting precision, recall, and median alarm-trigger latency for each of the three alarm modalities, together with the micro-averaged total and the false-alarm rate on the ten standard executions. The overall alarm precision is @@P_TOTAL@@ % and overall alarm recall is @@R_TOTAL@@ %, with @@FALSE_ALARMS@@ false alarms across the ten standard executions (a false-alarm rate of @@FAR_PCT@@ %). Median alarm-trigger latency is @@LATENCY_FRAMES@@ frames after the ground-truth onset (corresponding to @@LATENCY_SEC@@ s at the 30 FPS frame rate of Section 3.2). Per-alarm-type performance shows that @@COMMENT_BY_TYPE@@. Two practical observations follow. First, the alarm precision on standard executions confirms that the confidence-weighted observation update of Section 3.5 does not produce spurious alarms in the absence of true errors — a necessary condition for shop-floor deployability, where false alarms erode operator trust. Second, the @@LATENCY_SEC@@ s detection latency is well within the cycle-time tolerance of the assembly task; in particular, it is shorter than the lower bound of every per-step timing budget τᵢ used in this experiment, ensuring that the alarm reaches the operator before the next SOP transition. The pipeline's end-to-end behaviour on a representative abnormal sequence is visualised in Fig. 12.

**Table 10 — End-to-end alarm-level evaluation on twenty curated sequences (10 standard + 10 abnormal).**

| Alarm type | TP | FP | FN | Precision | Recall | Median latency (frames) |
|---|---:|---:|---:|---:|---:|---:|
| Ordering violation | @@OV_TP@@ | @@OV_FP@@ | @@OV_FN@@ | @@OV_P@@ % | @@OV_R@@ % | @@OV_LAT@@ |
| Timing violation | @@TV_TP@@ | @@TV_FP@@ | @@TV_FN@@ | @@TV_P@@ % | @@TV_R@@ % | @@TV_LAT@@ |
| Unfinished completion | @@UC_TP@@ | @@UC_FP@@ | @@UC_FN@@ | @@UC_P@@ % | @@UC_R@@ % | @@UC_LAT@@ |
| **Total (micro-averaged)** | @@TOTAL_TP@@ | @@TOTAL_FP@@ | @@TOTAL_FN@@ | @@P_TOTAL@@ % | @@R_TOTAL@@ % | @@LATENCY_FRAMES@@ |
| **False alarms on 10 standard executions** | — | @@FALSE_ALARMS@@ | — | — | @@FAR_PCT@@ % | — |

**Fig. 12 — Alarm-level timeline of the proposed framework on a representative abnormal sequence.**

---

#### Step A3-7:回填 §3.5 + §1 + Abstract(0.5 天)

把 §4.5 的"there now exists end-to-end alarm-level evaluation"这件事**反向传播**到:

1. **§3.5 末尾**(`"system-level evaluation that quantifies end-to-end alarm precision is beyond the scope of this paper and is discussed as future work in Section 5.3"`):**这句话现在过时了,要改**。改成:

   > "The end-to-end behaviour of the closed loop, including the alarm precision and recall over complete execution sequences, is reported in Section 4.5."

2. **§5.2 Limitations 第 1 条** 现在是 `"The state-machine layer is implemented as a deployed prototype but is not yet evaluated as a system-level metric..."` — **删掉这条**,因为 §4.5 已经评估了。改后 §5.2 变 2 个 limitations(few-shot 缺多种子 + 不能零样本迁移)。

3. **§5.3 Future work 第 1 条** 现在是 `"The first is an end-to-end evaluation of the system that consumes live video, exercises the full alarm pipeline, and reports alarm precision and recall over complete execution sequences."` — **这条要改**。因为现在已经做了 alarm-level eval,**剩下的是 live-video 完整流水线**。改成:

   > "The first is a real-time end-to-end evaluation of the deployed pipeline on continuous live video, extending the curated sequence-level evaluation of Section 4.5 to a stream of indefinite length with operator interaction in the loop."

4. **§1 Abstract** 加一句关于 alarm-level evaluation 的描述,放在 Grounding DINO 那句之后,deployment 那句之前:

   > "An end-to-end alarm-level evaluation on twenty curated execution sequences confirms that the closed-loop pipeline raises ordering, timing, and unfinished-completion alarms with @@P_TOTAL@@ % precision and @@R_TOTAL@@ % recall."

5. **§1 contributions (2)** 提到 FSM 部分,**追加一个数字**到末尾:

   > "...covering ordering violations, timing violations, and unfinished completion conditions; end-to-end alarm-level evaluation on twenty curated sequences reports @@P_TOTAL@@ % alarm precision and @@R_TOTAL@@ % recall (Section 4.5)."

**所有 @@…@@ 占位符跑完实验后一次性替换。**禁止在数字回来之前提交 docx。

---

## 3. 任务 B2 — VLM 推理速度 / GPU 占用量化(半天)

### 3.1 目标

在云端实测 Qwen2.5-VL-7B 在 4-bit NF4 quantisation 下的:
- 单帧推理时间(General mode + Verification mode)
- VRAM 占用
- Throughput(FPS)

### 3.2 实施

新建 `python/src/measure_inference_latency.py`:

```python
"""
Load fourpart_full_roi_mixed_fullsft_v2_rerun under 4-bit NF4.
Warm up 10 frames.
Measure 100 frames per mode:
  - General mode (full frame, action/tool/part prompt)
  - Verification mode (ROI crop, finish/unfinish prompt)
Report:
  - mean, p50, p99 latency (ms / frame)
  - VRAM usage (peak)
  - throughput (frames per second)
Output: python/output/eval/latency_v1/latency_summary.json
"""

import time
import torch
import json
from pathlib import Path

# ... (use evaluate_model.py-style loading)

def measure(mode: str, n_warmup: int = 10, n_measure: int = 100):
    # warm up
    for _ in range(n_warmup):
        ...
    torch.cuda.reset_peak_memory_stats()
    latencies = []
    for _ in range(n_measure):
        t0 = time.perf_counter()
        ...  # one inference call
        torch.cuda.synchronize()
        latencies.append((time.perf_counter() - t0) * 1000)  # ms
    peak_vram_gb = torch.cuda.max_memory_allocated() / 1e9
    latencies.sort()
    return {
        "mode": mode,
        "n_measure": n_measure,
        "mean_ms": sum(latencies) / len(latencies),
        "p50_ms": latencies[len(latencies) // 2],
        "p99_ms": latencies[int(len(latencies) * 0.99)],
        "peak_vram_gb": peak_vram_gb,
        "throughput_fps": 1000.0 / (sum(latencies) / len(latencies)),
    }
```

跑完后输出类似:
```json
{
  "general_mode": {"mean_ms": 320, "p50_ms": 310, "p99_ms": 420, "peak_vram_gb": 9.2, "throughput_fps": 3.13},
  "verification_mode": {"mean_ms": 280, "p50_ms": 275, "p99_ms": 350, "peak_vram_gb": 9.2, "throughput_fps": 3.57}
}
```

### 3.3 论文回填

§5.1 现有这段:

> "A full latency study is beyond the scope of this paper, but three system-level mitigations keep the inference budget tractable. First, the state machine throttles VLM invocations once an SOP step's completion is confidently established and concentrates calls around SOP transitions. Second, mode alternation halves the effective Verification-mode frequency. Third, 4-bit quantisation makes 7B-class VLMs deployable on a single mid-range GPU."

**改为:**

> "Latency is measured on a single mid-range GPU under the deployed 4-bit NF4 quantisation. Mean per-frame inference time is @@LAT_GENERAL@@ ms in the General mode and @@LAT_VERIFY@@ ms in the Verification mode (p99 @@P99_GENERAL@@ ms / @@P99_VERIFY@@ ms), with @@VRAM_GB@@ GB peak VRAM usage and an effective throughput of @@FPS_GENERAL@@ / @@FPS_VERIFY@@ frames per second respectively. Three system-level mitigations further keep the inference budget tractable: the state machine throttles VLM invocations once an SOP step's completion is confidently established and concentrates calls around SOP transitions; mode alternation halves the effective Verification-mode frequency; and 4-bit NF4 quantisation makes 7B-class VLMs deployable on a single mid-range GPU."

---

## 4. 任务 B4 — Timeline 可视化 Fig. 12(1–2 天)

### 4.1 目标

一张图,展示 §4.5 实验中**一段代表性 abnormal sequence** 的完整 FSM 状态演化 + alarm 触发点。

### 4.2 设计

**图结构(4 个子图垂直堆叠,共享 x 轴 = frame index):**

```
+-----------------------------------------------+
| (a) Per-frame VLM prediction                  |
|     stacked horizontal bars colored by part   |
|     showing General / Verification mode calls |
+-----------------------------------------------+
| (b) Per-node completion mass C_i(t)           |
|     line plot, one line per SOP node          |
+-----------------------------------------------+
| (c) Per-node error mass E_i(t) = C_i(1-F_i)   |
|     line plot, threshold 0.05 as dashed line  |
+-----------------------------------------------+
| (d) Alarms raised (vertical markers)          |
|     red x = ordering, orange + = timing,      |
|     blue * = unfinished                       |
|     overlay GT alarms as gray markers         |
+-----------------------------------------------+
```

X 轴:frame index(0 到 sequence length,~45 帧)。
Y 轴:各子图含义。

### 4.3 实施

新建 `python/src/plot_alarm_timeline.py`:

```python
"""
Read python/output/eval/fsm_end_to_end_v1/sequence_results.csv
for one representative sequence (suggest: "seq_abnormal_03" — an unfinished-completion case).
Plot 4-panel figure as described in §4.2.
Save as python/output/eval/fsm_end_to_end_v1/fig12_alarm_timeline.png
(also save .pdf for inclusion in docx)
"""
import matplotlib.pyplot as plt
# Style: Times New Roman, 300 dpi, white background — matches existing figures
plt.rcParams.update({
    "font.family": "Times New Roman",
    "font.size": 9,
    "figure.dpi": 300,
    "savefig.dpi": 300,
})
# ... 4-panel layout
```

### 4.4 插入 docx

把 PNG 文件 rsync 回本地 Mac,然后写一个 docx 插入脚本 `/tmp/insert_fig12.py`:

```python
from docx import Document
from docx.shared import Inches

DOC = '/Users/caiyunchen.3/vlma_paper_draft_v1_en.docx'
FIG_PATH = '/path/to/fig12_alarm_timeline.png'

doc = Document(DOC)

# Find the §4.5 results paragraph (the one ending with "is visualised in Fig. 12.")
# Insert a new paragraph after it, with embedded image, then a caption.
# Use the same pattern as existing figures in the docx.
...
```

**或者**让用户手动把图插到 Word 里(更稳)。

---

## 5. 任务 A5 — Alarm threshold 0.05 来源说明(半小时)

### 5.1 目标

在 §3.5 alarm 段(`"An ordering-violation alarm is raised when the error mass Eᵢ = Cᵢ · (1 − Fᵢ) ... exceeds 0.05"` 这段),加一句解释来源。

### 5.2 改法

A3 实验跑完后,如果发现 0.05 这个阈值真的是被 §4.5 实验验证过的(precision/recall 合理),就写:

> "The 0.05 threshold for both the ordering and timing alarm masses is selected to balance alarm precision and recall on a held-out calibration subset of the sequence-level evaluation introduced in Section 4.5; sensitivity of the alarm-level metrics to this threshold is reported as part of that evaluation."

如果跑出来发现 0.05 不够好,要调到比如 0.03 或 0.1,**先把阈值改成实际跑通的那个值,再写文字**。

### 5.3 改 §3.5 alarm 段

原文是:

> "An ordering-violation alarm is raised when the error mass Eᵢ = Cᵢ · (1 − Fᵢ) — capturing the situation in which a node is being credited with completion while its parents remain unfinished — exceeds 0.05;"

改成(假设最终阈值是 ε_E):

> "An ordering-violation alarm is raised when the error mass Eᵢ = Cᵢ · (1 − Fᵢ) — capturing the situation in which a node is being credited with completion while its parents remain unfinished — exceeds the threshold ε_E (set to ε_E = 0.05; calibrated on a held-out sequence subset as reported in Section 4.5);"

timing-violation 那句同理处理。

---

## 6. 任务 A6 — VLM Confidence Reliability Diagram(半天)

### 6.1 目标

证明 VLM 的 token-level confidence ρₜ 是 well-calibrated 的(或者诚实报告它不是)。

### 6.2 实施

新建 `python/src/measure_confidence_calibration.py`:

```python
"""
For each frame in the four-part held-out test set (112 frames in
roi_experiment_v2_4part/eval/test_full_v1.json), already have:
  - VLM prediction (Verification mode)
  - VLM confidence ρₜ
  - Ground-truth label

Compute:
  - Bin confidences into 10 equal-width bins on [0, 1]
  - For each bin: mean confidence vs mean accuracy
  - Expected Calibration Error (ECE):
      ECE = sum_bins (|bin_count| / total) * |mean_confidence - mean_accuracy|

Plot reliability diagram:
  X-axis: predicted confidence (bin centre)
  Y-axis: empirical accuracy in that bin
  Diagonal y=x reference line
  Bars: bin counts

Save: python/output/eval/calibration_v1/reliability_diagram.png
Print: ECE, MCE
"""
```

可以直接复用已有 evaluate_model.py 的输出(`all_predictions.csv` 已经有 prediction + GT 但**可能没 confidence**;如果没有,要重新跑一次 evaluation 同时记录 ρₜ)。

### 6.3 论文回填

**新建 Appendix D**(在 Appendix C 之后):

> **Appendix D. VLM confidence calibration**
>
> The SOP-guided state machine of Section 3.5 consumes the VLM's token-level confidence ρₜ as a soft observation weight; the calibration quality of this confidence therefore directly affects the alarm thresholds defined in Section 3.5. To characterise this calibration, the Full + ROI mixed checkpoint is evaluated on the four-part held-out test set (112 Verification-mode samples) with the predicted confidence recorded alongside the prediction. Fig. 13 shows the resulting reliability diagram. The Expected Calibration Error (ECE) is @@ECE@@ on a ten-bin equal-width binning of [0, 1], and the Maximum Calibration Error (MCE) is @@MCE@@. @@COMMENT@@. These calibration properties motivate the choice of soft-weighting (rather than hard thresholding) in the observation update rule of Section 3.5.

**新增 Fig. 13 caption**(在 Appendix D 段后):

> **Fig. 13 — VLM token-level confidence reliability diagram on the four-part held-out test (n = 112).**

---

## 7. 完成顺序和时间线建议

| 天 | 任务 | 输出 |
|---|---|---|
| Day 1 | Step A3-1 (SOP graph JSON) + Step A3-2 上半场 (FSM 类结构 + 单测) | `python/data/sop_graph_gearpump.json` + `python/src/fsm_state_machine.py` |
| Day 2 | Step A3-2 下半场 (FSM alarm logic 完整 + 通过 toy test) + A5 (alarm threshold 来源说明,等 A3 实验数据回来再回填) | FSM 模块完成 |
| Day 3 | Step A3-3 (20 sequence 构造 + GT 标注) + B2 (latency measurement) | sequences JSON + latency JSON |
| Day 4 | Step A3-4 + Step A3-5 (主实验 driver + 跑完) | sequence_results.csv + per_alarm_metrics.csv |
| Day 5 | Step A3-6 + Step A3-7 (回填 §4.5 / §3.5 / §1 / Abstract) + B4 (timeline 图) | docx 更新 + Fig. 12 PNG |
| Day 6 | A6 confidence calibration + Appendix D | reliability diagram + Appendix D 文本 |
| Day 7 | Audit + 报告 + 中文 docx 同步(本任务范围外,但顺便) | 0-error audit pass |

---

## 8. 完成验收

每个子任务完成的标志:

- [ ] **A3:** §4.5 完整新章节存在,Table 10 含真实数字,所有 `@@…@@` 占位符已替换;`python/output/eval/fsm_end_to_end_v1/per_alarm_metrics.csv` 存在,可被引用核对
- [ ] **B2:** §5.1 latency 段有具体 ms/FPS/VRAM 数字;`python/output/eval/latency_v1/latency_summary.json` 存在
- [ ] **B4:** Fig. 12 插入 docx,caption 在 §4.5 最后一段后面;PNG/PDF 源文件在 `python/output/eval/fsm_end_to_end_v1/` 下
- [ ] **A5:** §3.5 alarm 段提到 ε_E,有"calibrated on held-out sequence subset of §4.5"的来源说明
- [ ] **A6:** Appendix D 存在,Fig. 13 插入,ECE / MCE 数字真实
- [ ] `python3 /tmp/audit_en.py` 输出 0 errors
- [ ] 备份文件 `vlma_paper_draft_v1_en_BACKUP_before_<your-task-tag>_<date>.docx` 存在

---

## 9. 风险和已知陷阱

### 9.1 FSM 实现的边界情况

- **空 prediction**: VLM 在某些 frame 上可能 JSON 解析失败。这种情况要返回一个 dummy observation(`{"action": null, ...}`)并把 ρₜ 设为 0;**不要 skip**(skip 会破坏 timing budget 累积)。
- **多节点同时匹配**: 一个 action–object string 可能同时匹配多个 SOP 节点(比如多个 "tighten capscrew" 节点)。按论文 §3.5 描述,confidence-weighted probability 要**均分**到所有匹配节点。
- **Confidence ρₜ = 0**: 不能让一个节点完全不更新;实现里要确保即使 ρₜ → 0,Dᵢ 的累积逻辑还是按 wall-clock 时间走。

### 9.2 跑实验前必跑 dry run

写完 `run_fsm_end_to_end.py` 后,**先在 2 段 sequence 上跑通**,看输出 CSV 的列结构对不对,再跑全部 20 段。**不要一上来就跑 20 段然后发现 CSV 结构有问题**。

### 9.3 反直觉数据的处理

如果实验跑出来:
- **alarm precision < 70%**: 大概率是 FSM 实现的 bug(threshold 太低 / Eᵢ 公式错误)。**不要硬着头皮回填论文**,debug。
- **alarm recall < 70%**: 大概率是 GT 标注问题(expected_alarms 标偏了)或 alarm trigger 帧偏差超过 5 帧。先看 raw output。
- **false-alarm rate > 20%**: FSM threshold 太敏感。调阈值前先确认 §3.5 论文写的 0.05 这个数字到底是不是合适。

任何反直觉结果**先报告给用户,不要自己改数字**。

### 9.4 不要做的事(再次提醒)

- **不要重写 docx 的其他部分**(本任务范围严格限定在 §3.5 / §4.5 / §5 / Appendix D / Abstract / §1)
- **不要改实验已有结果**(§4.2.2 / §4.3.2 / §4.4 数字不动)
- **不要重新跑 Grounding DINO 实验**(已经跑过,数字在论文里了)
- **不要把模型权重 push 到 GitHub**(参考 `PAPER_HANDOFF.md` §8.1)

---

## 10. 联系 / 升级

- 用户偏好:**先用真数字,再说话**。任何"看起来对但没验证"的内容用户都会要求重做。
- 卡住怎么办:
  - 如果 FSM 实现 stuck > 1 天,把当前实现 + 报错 + 你考虑过但没试的方向写出来问用户
  - 如果跑实验跑了 2 小时还没出来,SSH 上去 `tail -f /tmp/<your-log>.log` 看在哪一步卡了
- 如果用户问"做完了吗",**给我具体的数字 + 文件路径 + checklist 勾掉的项**,不要含糊回答"做完了"

---

*文档结束。读完这份文档后,如果你(接力 agent)对任何一步不清楚,先停下来问用户,**不要凭猜测开始**。*
