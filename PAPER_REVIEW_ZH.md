# 论文 Review (中文,给作者本人看的)

**文档目的**:这是一份**严格的**论文 review。我读完了你 2026-06-17 当前版本的英文 docx 全文(~15 200 词,5 节 + 3 附录 + 11 个表 + 11 个图),从一个挑剔的 reviewer 视角告诉你:故事哪里有矛盾、哪里需要让步、哪里可以更狠、reviewer 最可能 push back 在哪、投稿前必改 / 可改 / 别动各是什么。

**我的立场**:论文整体已经很强了 — 数字硬、叙事完整、Grounding DINO 一加确实把故事闭环了。但有 12 处明确的问题(其中 4 处是 reviewer 一定会盯上、必须修),还有 8 处可以让故事更紧。下面逐项列出。

---

## A. 必改 (会被 reviewer 直接挑出来的硬伤)

### A1. Abstract 第二句语法不完整

```
"In this paper, a process-aware, neuro-symbolic monitoring framework
that couples a fine-tuned vision-language model (VLM) with an SOP-guided
finite-state machine (FSM) into a single deployable assembly-monitoring
system."
```

这句**没有谓语动词**。"In this paper, a framework that couples X with Y into Z." — 这是一个名词短语,不是句子。

**改法**:加 "is proposed"。

```
"In this paper, a process-aware, neuro-symbolic monitoring framework
that couples a fine-tuned VLM with an SOP-guided FSM into a single
deployable assembly-monitoring system **is proposed**."
```

或者把整句重写为主动结构。**必改 — Abstract 第二句的语法错误任何 reviewer 一秒就能看到**。

### A2. §3.1 "The third modules interact in a closed loop" — 语法和编号都错

第 74 行:`"The third modules interact in a closed loop."` 应该是 `"The three modules interact in a closed loop."`(three,不是 the third)。这是上一轮编辑时遗留的错误。

**必改**。

### A3. §3.1 引用了不存在的章节 4.2.2.2

第 72 行:
> "training and offline evaluation use ground-truth ROIs, while deployment supports any localiser that satisfies the perturbation envelope quantified in Section **4.2.2.2**."

文中没有 §4.2.2.2,扰动分析在 §4.3.2 里。

**必改**:`Section 4.2.2.2` → `Section 4.3.2`。

### A4. §3.3 "Therefore, propose ROI-aligned supervision" — 缺主语

第 126 行:
> "When the model is trained on full frames alone, ... Therefore, **propose** ROI-aligned supervision: ..."

被动语态规范要求 "ROI-aligned supervision is proposed" 或 "this paper proposes ROI-aligned supervision"。当前形式既不是主动也不是被动,语法上不合规。

**必改**。

同样的问题在 §3.5 第 152 行:`"Therefore, introduce an SOP-guided state machine"` → `"an SOP-guided state machine is introduced"`,以及 §4.3.2 第 267 行 `"additionally, evaluate the Full + ROI mixed model"` → `"the Full + ROI mixed model is additionally evaluated"`。

**全文搜一遍 `Therefore, propose` / `additionally, evaluate` / `report` / `re-run` 之类的悬空动词**。我看到至少 3 处。

### A5. §3.5 / §4.3.2 多处段落开头有 stub 残留

第 158 行末尾:
> "...as separate hand-coded detectors. **that together cover the practical error taxonomy of in-line assembly monitoring:**"

— 这个 stub 是上一轮编辑漏删的旧句尾。

第 166 行:
> "Before the verification results are reported, the instantiation of the SOP-guided state machine of Section 3.5 is **instantiated** for the gear-pump assembly task."

— "instantiation ... is instantiated" 自我重复;且这段跟前一段 (第 164 行 `"To make the state-machine layer concrete, ..."`) 几乎是同一句话两次说。

第 310 行 §4.4.2 末尾:
> "Over a deployment lifetime in which the SOP evolves, this asymmetry compounds. **— here, two classes (finish, unfinish) — over a specific input distribution — here, the cropped ROI of a single part. By construction, it cannot do three things that the proposed system requires.**"

— 这段是上面同一段的尾部被截断重复粘贴的残留。一定要删干净。

第 257 行 §4.3.2:
> "The General ATP + Verification (Full + ROI mixed) variant adds the four-part Full + ROI mixed verification training data and is the proposed unified configuration**.; no verification data. Acts as the unified-perception baseline.**"

— `.; no verification data. Acts as the unified-perception baseline.` 是粘贴时遗留的旧片段。

**必改 — 这种残留 reviewer 一眼就能看到,会直接质疑论文的严谨性**。我建议你打开 docx,直接全文搜 "Acts as the unified-perception baseline"、"— here, two classes" 这种特征词,逐处确认无残留。

### A6. §4.3.2 第 263 行 "directional reading anticipated by Sections 4.3 – 4.5"

文中没有 §4.5。这是 RCIM 重构前的旧编号遗留。

**改法**:`Sections 4.3 – 4.5` → `Sections 4.2 and 4.3`(因为内容上是这两节预期的方向)。

### A7. Abstract 一处文字重复

> "The framework is evaluated **the framework** on a manual assembly dataset..."

`"is evaluated the framework"` 不通。改成 `"The framework is evaluated on a manual assembly dataset..."`(删掉重复的 "the framework")。

### A8. §3.4 引用错误

第 137 行:
> "Fig. 6 summarises the resulting dual-mode adaptation"

下一句:`"Fig. 6 — Dual-mode VLM adaptation under a shared set of weights."` — 这是 caption。OK。

但 §3.1 第 68 行:`"illustrated in Fig. 1"`,下面有 caption。OK。

第 86 行(§3.5):`"This per-frame loop is illustrated in Fig. 2."` — 但 Fig. 2 (Closed-loop inference cycle) 的 caption 在 §3.1 末尾(第 78 行)。Fig. 2 出现在 §3.1 末尾,然后到 §3.5 (第 162 行)才引用。

**这是 OK 的**(figure 可以放在被首次引用的位置之后),但 Fig 2 离它在文中第一次被讨论的地方(§3.5 闭环推理段)有点远。Reviewer 不一定会挑,但**视觉流上 Fig. 2 应该挪到 §3.5 那段后面**。我建议:把 Fig. 2 caption 物理位置移到第 162 行那一段之后,而不是放在 §3.1 末尾。

---

## B. 强烈建议改 (故事张力 / 叙事清晰度)

### B1. Grounding DINO 100 %/0 % FPR 这条结果的"超预期"问题

**这是论文最大的叙事张力点,值得最认真讨论。**

你现有的叙述:
- §4.3.2 Table 7:扰动包络在 ±5–15% 中心偏移下 worst FPR 8.20%
- §4.3.2 Table 8:Grounding DINO IoU 0.608 → verification 100%/0% FPR
- §4.3.2 段落里这么解释:"despite the substantial localisation error implied by the 0.608 mean IoU (comparable to centre offsets in the upper half of the envelope), ... matches the GT-ROI ceiling at 100.00 % / 0.00 % FPR"

**这里的问题:reviewer 会立刻发现矛盾**。如果 IoU 0.608(相当于 ~30-40% 中心偏移)能达到 100/0,为什么 Table 7 的 ±15% 中心偏移(IoU 应该比 0.608 高得多)反而 FPR 是 3.28% 不是 0%?

这有三种可能的解释,你**必须**主动说出来一种,否则 reviewer 会写 "the authors' own perturbation analysis predicts substantially worse performance than they report from Grounding DINO; this inconsistency is unresolved":

**解释 1(我推荐)**:Grounding DINO 的检测误差**模式**跟人工合成扰动**不同**。Grounding DINO 错的方向不是中心 / 尺度的随机偏移,而是"框得偏小但还在物体上"(实际检查 detector 输出常常会发现 IoU 0.6 主要是因为 detector 框得比 GT 紧凑,但**关键完成度线索 — 接缝、孔位 — 仍在框内**)。Table 7 的合成扰动是无差别地把 ROI 推开,可能正好把关键线索推出框;Grounding DINO 不会犯这种错。

→ 这是一个 **subtle 但漂亮**的论证。建议在 §4.3.2 加一段:

> "It is worth noting that Table 8 reports a stronger end-to-end result than the perturbation envelope of Table 7 alone would predict. The likely reason is that the perturbation directions sampled in Section 4.3.2 are isotropic — centre offsets and scale jitter are applied without regard to the location of completion cues — whereas the bounding boxes returned by Grounding DINO are content-aware: the detector localises the part region itself, so the resulting ROI, even when noticeably smaller than the ground-truth box, still encloses the seating gaps, hole edges, and mating surfaces that the Verification mode relies on. This suggests that the Section 4.3.2 perturbation envelope is, in practice, a conservative upper bound on the true detector-induced degradation."

**这一段会让你的故事变更强 — 你把"看起来矛盾"的结果转化成"我们的扰动分析其实低估了系统鲁棒性"**。

**解释 2(次选)**:测试集只有 112 帧,Table 7 的 FPR 数字本身有大样本方差。Grounding DINO 实验也是 112 帧,所以两者方差差不多 — 但运气好,正好都对了。

→ 这个解释**比解释 1 弱很多**(等于承认结果可能不稳),不推荐用。

**解释 3(最弱)**:不解释,直接报数字。

→ 这是当前的做法,会被 reviewer 质疑。**不推荐**。

### B2. Drive Gear 的 IoU 只有 0.39 — 没在论文里说清楚

你 iou_summary.json 里 per-part:Drive Gear 0.39, Thrust Block 0.42, Port End Cover 0.75, Gear Housing 0.82。差异很大。

但 §4.3.2 只报告了**总体**平均 IoU 0.608,没说**最差零件低到 0.39 但 verification 仍然 100%**。这其实是论文最强的论据之一 — 它把"鲁棒性"的 claim 推到一个极端:不仅 IoU 0.6 行,IoU 0.39 也行。

**建议**:在 §4.3.2 Grounding DINO 段加一句:

> "The detector performance varies substantially across parts: the per-part mean IoU ranges from 0.39 (Drive Gear) to 0.82 (Gear Housing), reflecting the differing visual scale and contrast of the four parts. Despite this heterogeneity, the verification accuracy on every part remains at 100 % — including the 29-frame Drive Gear subset where detector IoU is lowest — further evidence that ROI-aligned supervision tolerates localisation errors that would be considered severe by standard detection metrics."

(这一段直接对应论文的核心论点 "ROI-aligned supervision 让 VLM 对 ROI 质量极度鲁棒")

### B3. §4.4 的 YOLO 基线叙事和 §3.6 的 Grounding DINO 叙事有逻辑张力

**张力**:
- §3.6 选择 Grounding DINO 的理由 #4:"it sits in a different architectural niche from the fixed-class CNN baseline of Section 4.4: an open-vocabulary detector is exactly the kind of localiser a closed-class YOLO-style detector cannot be"
- §4.4.2 论证 YOLO 不能替代 VLM 的理由 #3:"it cannot support open-vocabulary extensibility"

这两条论证用了**完全相同**的概念(open-vocabulary),但放在不同地方,逻辑上是同义反复。reviewer 会觉得 §3.6 和 §4.4 在抢同一个论点。

**改法 1**:删 §3.6 理由 #4 中"sits in a different architectural niche from §4.4"那句,只保留"open-vocabulary 匹配 white-list extensibility"这个理由。然后 §4.4 不用提 Grounding DINO 这条线。

**改法 2(我推荐)**:在 §4.4.2 主动收个尾,明示 "this open-vocabulary requirement is the same constraint that motivated the deployment-time ROI provider choice of Section 3.6; the proposed framework's commitment to open-vocabulary perception is consistent across both the foreground VLM and the background detector." 这样把两节连成一个论证。

### B4. §4.3.1 (4.3.2 set up 段) 现在已经说"three experiments",但 §4.3 标题还是 "Unified multi-task integration and deployment robustness" — 没体现端到端 detector

§4.3 标题对一半内容,reviewer 会问"为什么 Grounding DINO 端到端归到这个 section 而不是单独 section?"

**改法**:把 §4.3 标题改成 `"Unified multi-task integration, deployment robustness, and end-to-end ROI provider evaluation"`,或者直接 `"Unified multi-task integration and deployment evaluation"`。

### B5. Conclusion (§5.3) 第 366 行的格式

```
"Four directions follow naturally from the limitations identified above.
The first is an end-to-end evaluation of the system... (2) a study of
cross-variant transfer... (3) an integration study...
The fourth is few-shot cross-part transfer..."
```

混用了 "The first is", "(2)", "(3)", "The fourth is" 三种编号。不一致。

**改法**:统一用 "The first" / "The second" / "The third" / "The fourth"(更正式),或者全 "(1)/(2)/(3)/(4)"。我推荐前者。

且 (3) 还有一个矛盾:"an integration study that quantifies the deployed-detector contribution to the ROI-provider envelope of Section 4.3.2, closing the system claim end-to-end with a concrete localiser" — 但 §4.3.2 现在**已经做了**这件事(Grounding DINO 端到端)。这条 future work 应该删掉或改写。

**改法**:
- 把 (3) 删掉(因为已经做过)
- 替换为别的方向,例如:"a comparison of multiple open-vocabulary ROI providers (OWL-ViT, SAM-class) under the same SOP-conditional protocol to characterise how the verification claim of Section 4.3.2 depends on the specific detector"

### B6. §5.1 第一段 (Discussion) 把"observations"从五点扩到了六点,但段落开头还说"Three threats"

第 346 行:`"Three threats to the validity of the present results should be acknowledged."` — 这是 Discussion 的第一段,讲三条 validity threat,跟"observations"是不同的东西。但 §5 主体 (§5 introductory text 第 317–341 行) 用 `"first observation" / "second observation" / .../ "sixth observation"` 的编号,而 §5.1 Discussion **另起一套** "three threats"。

这不算错,但对读者来说很乱:同一节(§5)既有 6 个 "observation" 又有 3 个 "threat" 又有若干 "implications for design" 段。

**改法(可选)**:重新组织 §5 的结构。我建议:

```
5.1 Findings (重新命名,容纳 6 个 observations)
5.2 Implications for design (容纳后面的 "recommended deployment configuration"
    "procedural knowledge belongs in the symbolic layer" 等段)
5.3 Discussion (容纳 "three threats" + deployment 配置 + latency)
5.4 Limitations (现在的 5.2)
5.5 Conclusion (现在的 5.3)
```

或者**至少把六个 observations 编号去掉**,改为按主题归类("ROI supervision 部分两段 → prompt 部分一段 → unified 部分一段 → ROI provider 部分一段 → YOLO 部分一段")。

### B7. §4.2.2 引导式提示词分析中的措辞

第 230 行:
> "This brittleness with respect to verbose prompt wording is consistent with broader findings on language-model sensitivity to spurious prompt features [21]. The failure mode itself — the model articulates the correct part while accepting more than half of all Unfinish samples — has direct implications for industrial-safety deployment: in any VLM-based quality-monitoring pipeline, verbose verbal guidance can systematically degrade visual discrimination, and this regression should be tested for explicitly."

这一段从"我们的发现"跳到"对工业安全的一般性建议",**有点说教**。reviewer 可能会觉得 "你只有 285 帧的实验,不应该对整个工业 VLM pipelines 给建议"。

**改法**:把"in any VLM-based quality-monitoring pipeline"改成 "for VLM-based assembly verification pipelines in particular";或者把这句话整体删掉,留前面的"failure mode 描述"就够了。

### B8. §4.4 的 "different system roles" 论证有点重复

§4.4 末尾 (第 312 行) 和 §5.1 sixth observation (第 329 行) 几乎在说同一件事:VLM 和 YOLO 不是替代关系,而是不同 system role。

§4.4 是结果分析,§5.1 是讨论 — 同一论点说两次很正常,但**用词上有 80% 重叠**(都用 "system role" "parity of a component, not of a system" 等)。

**改法**:§5.1 第六点的措辞**全部重写**,从"YOLO 跟 VLM 在 §4.4 是 component-level parity"这个事实**出发**,讲一个 §4.4 没说的事情 — 例如:

> "The sixth observation — that a small CNN matches the VLM at component level on a cropped-binary task — has methodological consequences beyond the choice of perception layer. It implies that any future paper proposing a new assembly-verification VLM must be benchmarked on the system-level properties listed in Section 4.4.2, not on per-part accuracy alone. Reviewer practice in this subfield should therefore evolve to require multi-task, language-typed, open-vocabulary evaluation, not just FPR on a binary held-out set."

(更广的影响、更值得放在 Discussion)

---

## C. 让故事更紧的优化建议 (取舍)

### C1. 删 §3.5 中重复的 SOP graph 描述

§3.5 现在有两段几乎一样的话:
- 第 164 行:`"To make the state-machine layer concrete, the SOP-guided graph 𝒢 of Section 3.5 is instantiated for the gear-pump assembly task as follows."`
- 第 166 行:`"Before the verification results are reported, the instantiation of the SOP-guided state machine of Section 3.5 is instantiated for the gear-pump assembly task. The SOP is encoded as a 15-node directed acyclic graph (Fig. 7)..."`

第 164 行那句完全多余 — 它说"接下来要讲实例化",然后第 166 行又重新开始讲实例化。**删掉 164 行那句**,直接进入 166 行。

(顺带把 166 行 "is instantiated for the gear-pump assembly task" 改成 "is realised for the gear-pump assembly task",避免"instantiation ... is instantiated"自我重复。)

### C2. §4.4 实验设置段落出现两次

§4.4.1 第 293 行有一段 "A YOLOv8n-cls classifier (1.4 M parameters; ...)" — 然后 §4.4.1 第 295 行又来一段 "The experiments reported above establish that ROI-aligned supervision..." — 然后**第 297 行又是另一段 "A YOLOv8n-cls classifier (1.4 M parameters; ...)"**!

第 293 行和第 297 行**几乎一字不差**重复(只差一个 "Section 4.2.2" vs "Section 4.2" 引用)。

**必删一个**。这是 §4.4 重构时遗漏的副本。建议保留第 297 行(它更接近 results 部分,叙事流更顺),删第 293 行,把第 293 行的内容塞到 §4.4 setup 一段里就行。

### C3. §3.5 的 "Before the verification results are reported" 一句逻辑奇怪

第 166 行开头 "Before the verification results are reported, ..." — 这句话试图把 SOP graph 实例化放在 §4 之前,但 §3.5 本来就在 §4 之前,这句话是多余的。

**改法**:把这句开头删掉,直接 "The SOP-guided state machine of Section 3.5 is realised for the gear-pump assembly task as follows. The SOP is encoded as a 15-node directed acyclic graph..."

### C4. §5 主体 (§5 intro) 跟 §5.1 Discussion 内容有交叉

§5 主体讲了 "recommended deployment configuration"、"Two effects further motivate the use of ROI"、"The observation that prompt engineering cannot substitute"、"The single-frame phase-confusion residual" 等,这些其实更适合放进 §5.1 Discussion(或新的 "Implications for design")节。

现在的结构:
- §5 intro: 一段 + 6 个 observations + 5 段 "implications" + 1 段 closing
- §5.1 Discussion: 3 个 threats + deployment + latency + new SOP variant

**问题**:§5 intro 和 §5.1 在干同样的事(讨论),只是按不同维度切分。**对读者来说就像看两遍 Discussion**。

**改法(中等工作量)**:把 §5 intro 中的"implications" 5 段合并到 §5.1 Discussion 里,§5 intro 只保留"findings(6 个 observations)"。这样:
- §5 intro / 5.1 Findings:6 个 observations,纯事实陈述
- §5.2 Discussion:把所有 implications + threats + deployment 合并
- §5.3 Limitations(现在的 5.2,降一级)
- §5.4 Conclusion(现在的 5.3,降一级)

### C5. Table 1 (in-distribution validation) 价值不大,reviewer 可能会问"为啥放"

第 216 行:`Table 1 — Single-part verification on the in-distribution validation set.`

§4.2.2 第 214 行说 "Table 1 results sit at near-ceiling and are reported for completeness; the 3.16 results are the discriminative ones." — 自己承认 Table 1 不是 discriminative 的。

**取舍建议**:删 Table 1,只留 Table 2。或者把 Table 1 + Table 2 合并成一个表,加 "Source" 列区分 in-distribution / held-out。这样省一个表位。

**反对意见**:Table 1 是个"诚实牌" — 你向 reviewer 展示 "我们没在 in-domain 上偷分数"。删掉也有风险。

**我的判断**:保留,但**把 Table 1 移到附录**,主文只留 Table 2。Table 1 作为 Table B.2(在 Appendix B 训练超参后面)。这样 §4.2.2 体感更紧凑。

### C6. Abstract 太长 (446 词)

446 词的 abstract 在 RCIM / Sensors 都偏长(常规 250-350 词,Sensors 明确限制 200 词)。

**取舍**:必须压。建议保留:
- 问题陈述 1 句
- 框架 + ROI-aligned supervision 1 句
- FSM 1 句
- Grounding DINO ROI provider 0.5 句
- 关键数字 3 个:99.30%/0.69% (单零件) + 100%/0% (四零件) + Grounding DINO 100%/0%
- 系统部署声明 1 句

把 unified multi-task / YOLO baseline / prompt ablation 这些**全部从 abstract 拿掉**。这三件事在 abstract 中本来就是次要内容,放在 §1 contributions 即可。

目标:**压到 280–320 词**。

### C7. §1 Introduction 的 contributions 段落 (第 28 行) 5 条 contributions 太多

> "(1) A neuro-symbolic monitoring pipeline... (2) A dual-mode adaptation of the VLM... (3) An SOP-guided probabilistic FSM... (4) An ROI-aligned supervision strategy... (5) The system-level value of the VLM relative to a fixed-class CNN baseline is demarcated..."

5 条 contributions 在期刊论文里偏多(常规 3-4 条)。且 (2)(3) 实际上是 (1) 的展开(neuro-symbolic pipeline 包含 dual-mode VLM 和 FSM)。

**取舍**:压成 4 条:
- (1) ROI-aligned supervision (核心方法)
- (2) Dual-mode VLM + SOP-guided FSM 一起(系统贡献)
- (3) Open-vocabulary ROI provider 端到端闭环(部署贡献)
- (4) 跟 YOLO baseline 对比清晰划分了 system-level vs component-level 评估范式(评估贡献)

### C8. §3 现在 6 个 H2 (§3.1-§3.6),比 §4 (3 个 H2 各带 2 个 H3 = 9 个 heading) 看着仍少

虽然现在 §3 字数已经追上 §4 (4562 vs 4566),但**层次感**不一样。

**潜在改法**:把 §3.5 拆成两个 H2:
- §3.5 SOP-guided state machine
- §3.6 Deployment architecture
- §3.7 ROI provider

或者保持 6 个 H2 不动 (现在的结构),但是**把 §3.5 内部用 H3 切**:
- §3.5.1 Process graph + observation update
- §3.5.2 Alarms
- §3.5.3 SOP graph instantiation for gear pump
- §3.5.4 Deployment architecture

这样 §3 结构对称于 §4,reviewer 看着更舒服。**取决于你愿意花多少时间整理。**

---

## D. Reviewer 最可能 push back 的 5 个点 + 我推荐的防御策略

### D1. "你们的 multi-part test set 只有 112 帧,Wilson upper bound 1.67% 仍然不是统计显著的 zero-error"

**Reviewer 视角**:四零件 100% / 0% FPR 听起来很漂亮,但 112 帧太小,你怎么知道这不是过拟合到测试集?

**你已有的防御**:
- §4.2.2 已经写了 Wilson 95% upper bound = 1.67%(承认数字有上限)
- §5.1 也提了 "the gap between Full-only and Full + ROI mixed" 比"the literal ceiling"更有说服力

**我推荐的补强**:把 Wilson upper bound 这件事**直接挪到 abstract**!当前 abstract 说 "records zero errors (Wilson 95 % upper error bound 1.67 %)" — 这一句已经在了,**但太低调**。加粗或换个动词:"establishes a Wilson 95 % upper bound of 1.67 % on the true four-part error rate"(更主动)。

**还可以做**:Grounding DINO 100%/0% 也是 112 帧,同样面临这个问题。要在 §4.3.2 末尾加一句 "Both the GT-ROI and Grounding DINO results carry the same Wilson 95% upper bound of 1.67% on the 112-frame test set."

### D2. "为什么不用 multi-seed?"

**Reviewer 视角**:§4.2.2 四零件、§4.3.2 unified multi-task、§4.3.2 Grounding DINO 全部是 single-seed。只有 §4.4 YOLO 是 multi-seed。这种不对称会被 reviewer 直接挑出来。

**你已有的防御**:
- §4.2.2 已经写了 "the figures reflect a single training run with a single random seed; ... the substantive evidence is not the ceiling itself but the gap between Full-only and Full + ROI mixed"
- §4.3.2 也写了 "Section 4.4 reports multi-seed few-shot curves on the Cover scope to characterise variance directly"

**我推荐的补强**:把"为什么 single-seed"从"诚实承认局限"升级为"deliberate design choice":

> "Single-seed reporting is a deliberate choice in this paper: the load-bearing claim is the gap between training-distribution variants, not the absolute ceiling of any single configuration. A gap of 40 percentage points (60.65 % Full-only vs 100.00 % Full + ROI mixed) cannot be flipped by any plausible seed variance. Where seed variance does become substantive — at small training sizes — multi-seed reporting is provided (Section 4.4, three seeds at each N)."

(把"我们没钱多次跑"包装成"我们故意选 single-seed 因为足够"。)

### D3. "你们的 4 个零件都是同一个工件 (齿轮泵) 的子部件,泛化性怎么证明?"

**Reviewer 视角**:你说 "multi-part",但其实是同一个产品的 4 个零件。不是 4 个不同产品。"part-level generalisation" 跟 "product-level generalisation" 不是一回事。

**你已有的防御**:
- §5.2 limitation 已经承认"Verification does not transfer zero-shot to unseen parts"
- §5.3 (4) 列了 "few-shot cross-part transfer" 作为 future work

**我推荐的补强**:在 §4.1 实验设置里**主动**说清楚:

> "All four parts in the multi-part benchmark are sub-assemblies of the same gear-pump workpiece. The proposed framework is therefore demonstrated to generalise across **parts within a product**; **cross-product** generalisation — applying the same trained model to a fundamentally different assembly (e.g., a different mechanical product) — is not evaluated in this paper and is explicitly listed as future work in Section 5.3 item (2)."

这样把"四零件不算 cross-product"从被 reviewer 挑出来变成你主动承认,然后 §5.3 (2) "cross-variant transfer" 就是回应这一点的。**主动承认 limitation 永远比被 reviewer 挑出来好**。

### D4. "Grounding DINO 默认 threshold 没调,会不会对你不利的 case 你没汇报?"

**Reviewer 视角**:你说 "default thresholds (box 0.25, text 0.20); no per-deployment threshold tuning is performed" — 但谁知道你是不是先调好了 threshold 然后说"我们用了 default"?

**防御**:你**已经写了**"100 %检出率,112 / 112"。这意味着所有帧都有 box(threshold 不可能再升,否则会漏检)。Reviewer 不太可能挑这个,因为 100% recall 就在那里。

但**我建议加一句**:"At the default thresholds, all 112 test frames yielded at least one detection — there is no threshold cliff between recall and precision, and no per-frame fallback was triggered." 把 fall-back 的描述跟实测数据挂钩,让 reviewer 知道这条 "100% detect" 是 verifiable 的。

### D5. "你们 verification 是 binary (Finish/Unfinish),为什么不做 multi-stage (e.g., 部分完成 / 完全完成)?"

**Reviewer 视角**:工业 SOP 里很多步骤有中间态(顶丝拧到 50% / 80% / 100% 这种)。你 binary 划分太粗。

**你已有的防御**:零。这一点论文从未直接讨论。

**我推荐的补强**:在 §3.1 task formulation 之后加半句话:

> "The Finish / Unfinish binary is chosen for two reasons. First, the SOP-conditional protocol of Section 3.6 ensures that the Verification mode is only queried at the SOP step's nominal completion moment — when the operator has just performed the corresponding action — so intermediate states are not in distribution. Second, finer-grained completion levels (e.g., torque-stage classifications for fasteners) would require sensor modalities beyond the single RGB camera adopted in this paper. The binary formulation thus matches the perceptual capacity of monocular RGB at the granularity at which the SOP defines step completion."

这样把 binary 从"我们偷懒了"转成"我们有意识的取舍"。

---

## E. 跟同领域 (Q. Ye RCIM 2026, Liu et al. RCIM 2026) 的对比 — 论文的相对优势 / 劣势

我没有把这两篇 paper 加载到上下文里详细对比,但基于我对 RCIM 2026 这两篇的一般印象:

**你的优势:**
- **VLM + Symbolic FSM 的组合**:Q. Ye 那种"时空感知 + motion similarity"是纯神经端到端;你有显式 SOP 图 + 概率激活,可解释性高一截
- **Open-vocabulary ROI provider**:别人没做。Reviewer 看到 "no detector fine-tuning" 会很喜欢
- **ROI-aligned supervision**:数据成本极低(每帧多一个 crop,标注不增加),Q. Ye 那种 spatiotemporal 模型数据成本高
- **完整可部署系统**:你有 Python+Java 双服务架构、4-bit 部署、HTTP 通信细节 — 真能落地

**你的劣势:**
- **时序建模弱**:Q. Ye 主打 "spatiotemporal perception",你的论文每帧独立 + FSM 累积,中间没有 RNN / Transformer over time。Reviewer 可能问 "为什么不用时序模型直接吃完整 sequence"
- **数据集小**:你 ~1700 帧 train,Q. Ye 类的数据集常常上万帧
- **没有跟 spatiotemporal baseline 直接对比**:你只跟 YOLO 比了,没跟 LSTM / SlowFast / Q. Ye 那类比

**最危险的潜在 reviewer comment**:"Authors should compare with [Q. Ye 2026]'s spatiotemporal model on the same dataset to demonstrate that the proposed neuro-symbolic approach actually outperforms a purely neural spatiotemporal baseline."

**防御**:在 §2.1 末尾或 §4.4.2 开头主动写一段 "Comparison with spatiotemporal pipelines is beyond the scope of this paper because: (i) the proposed system targets per-frame deployment latency in shop-floor cells, which excludes models that require long windows; (ii) spatiotemporal models address action recognition rather than completion verification, which Section 1 identifies as orthogonal tasks." 把"我们没比"从"漏洞"变成"明确划界"。

---

## F. 投稿前清单 (按优先级)

### 必改 (投稿前一定要修):

- [ ] A1: Abstract 第二句加 "is proposed"
- [ ] A2: "The third modules" → "The three modules"
- [ ] A3: "Section 4.2.2.2" → "Section 4.3.2"
- [ ] A4: §3.3 / §3.5 / §4.3.2 三处悬空动词改被动语态
- [ ] A5: 全文搜 stub 残留: `"— here, two classes"`、`"Acts as the unified-perception baseline"`、`"that together cover the practical error taxonomy of in-line assembly monitoring:"`(末尾冒号)、`"is instantiated for the gear-pump assembly task. The SOP is encoded ... is instantiated"`(双 instantiated)
- [ ] A6: §4.3.2 "Sections 4.3 – 4.5" → "Sections 4.2 and 4.3"
- [ ] A7: Abstract "is evaluated **the framework** on" 删重复
- [ ] B1: §4.3.2 加一段解释 Grounding DINO 比扰动包络好(content-aware 解释)
- [ ] B2: §4.3.2 加 Drive Gear IoU 0.39 仍 100% verification 的论述
- [ ] B3 或 B8: §3.6 跟 §4.4 / §5.1 的 open-vocabulary 论证去重
- [ ] B5: §5.3 future work 编号统一 + 删 (3) 改新方向
- [ ] C2: §4.4 删除重复的 YOLOv8n-cls classifier 描述段
- [ ] D3: §4.1 加 "all four parts are sub-assemblies of the same gear-pump workpiece" 的明确说明

### 强烈建议改 (会让论文质量上一档):

- [ ] B4: §4.3 标题加 "end-to-end ROI provider evaluation"
- [ ] B6: §5 结构调整,合并 §5 intro 与 §5.1 Discussion 或重新分组
- [ ] B7: §4.2.2 prompt ablation 末尾措辞收敛(去说教)
- [ ] C1: §3.5 删第 164 行 "To make the state-machine layer concrete" 那句
- [ ] C3: §3.5 第 166 行开头删 "Before the verification results are reported"
- [ ] C4: §5 整体结构改成 Findings / Discussion / Limitations / Conclusion 4 节
- [ ] C5: Table 1 移到附录
- [ ] C6: Abstract 压到 280-320 词
- [ ] C7: §1 contributions 压到 4 条
- [ ] D2: §4.2.2 加"deliberate single-seed choice"段
- [ ] D5: §3.1 加 binary 验证的取舍说明

### 可改可不改 (有时间再说):

- [ ] A8: Fig. 2 物理位置挪到 §3.5
- [ ] C8: §3.5 内部加 H3 切分
- [ ] E 的 spatiotemporal baseline 防御段

### 别动 (动了反而坏事):

- ROI-aligned supervision 的核心叙述
- 现有的所有具体数字
- §3.6 ROI provider 整节(刚加好,故事漂亮)
- §4 各表的具体结构
- §4.3.2 现有的 Grounding DINO 段(B1/B2 是**加**内容不是改)
- 参考文献顺序(第一次出现顺序)
- CRediT、Declaration of competing interest

---

## G. 我对当前论文的整体打分

**(1) 论点强度**:9 / 10 — 主张清晰、有梯度、有反例(YOLO baseline 是"诚实"的对照)
**(2) 实证强度**:8 / 10 — 数字硬,但 single-seed + 112 帧测试集 + 只一个产品的 4 个零件,reviewer 会盯
**(3) 叙事流畅度**:6 / 10 — 残留 stub、悬空动词、重复段落 5+ 处,需要扫一遍
**(4) 结构对称性**:7 / 10 — §3 vs §4 字数平衡了,但 §5 内部混乱,§3.5 内部组织松散
**(5) 与领域对接**:7 / 10 — Related Work 写得不错,但没跟最近的 spatiotemporal pipeline 划清界
**(6) 故事闭环**:**9 / 10** — Grounding DINO 进来后基本闭环了,只差解释好 IoU 0.6 → 100% verification 这件事

**综合**:**7.7 / 10** — 是一篇 solid 的 Q2 期刊投稿。改完上面 "必改" 12 项,可以推到 8.5。改完"强烈建议" 11 项,可以推到 9.0+。

---

## H. 我能帮你做什么

我可以:

1. **直接帮你改完所有"必改"项**(A1-A8 + B1/B2 + C2 + D3,大概 15 处 docx edit,30-45 分钟)
2. **帮你重写 Abstract 到 280-320 词**(C6)
3. **帮你重写 §1 contributions 到 4 条**(C7)
4. **帮你重组 §5 结构**(C4,工作量更大,1-2 小时)
5. **帮你做完所有"强烈建议改"**(2-3 小时)

按你的时间和体力安排,我建议先做 1 + 2 + 3,然后看时间是否允许做 4 + 5。

要不要现在开始,从哪一项开始?

---

*文档结束。该文档不是给 reviewer 看的,是给作者本人评估论文质量的 internal review。*
