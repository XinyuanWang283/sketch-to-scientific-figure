# Start here / 从这里开始

## 当前默认流程

这个 repository-scoped Skill 帮科研人员把一张手绘科学草图先变成 **5 个可比较的视觉方向**，选定后再重建为可编辑科学图：

> 手绘草图 → Codex 聚焦提问 → 5 次分别调用内置 ImageGen → 研究者选择/修改 → 显式批准 → 原生可编辑 SVG/PPTX 重建 + experimental draw.io 结构视图 → PDF 预览 → 最终人工检查

**AI 提方案，科研人员做决定。** 你不需要先审查 structured interpretation、JSON、truth contract 或 deterministic skeleton。内部语义元数据只在选定候选后用于稳定重建和验证，不是用户前置作业。

## 最快使用方法

1. 在可使用内置图像生成的 Codex App 会话中打开本仓库，附上手绘草图。
2. 说明必须精确保留的标签、公式、箭头含义或敏感内容边界。
3. 调用：

```text
$sketch-to-scientific-figure
```

4. Codex 先检查草图和已有对话，每轮只问 1–3 个真正会改变结果的问题，通常不超过两轮。
5. 信息齐全后，Codex 用同一张草图和同一份简短自然语言 brief，分别调用 5 次内置 ImageGen。
6. 你可以直接说 `Choose C`、`Revise C`、`Use C's layout with A's colors` 或 `Regenerate all five`。
7. 只有在你明确批准一个方向后，才开始可编辑重建。

默认 live 路径使用 **Codex 内置 ImageGen**，不要求你提供 `OPENAI_API_KEY`，也不由仓库 Python 代码伪装调用图像模型。

## 固定的 5 个候选

| 槽位 | 方向 | 主要目的 |
|---|---|---|
| A | Faithful | 尽量保留手绘布局与识别特征，做专业化润色 |
| B | Publication | 紧凑、克制、适合论文图幅 |
| C | Presentation | 强调层级与远距离可读性，适合 Science Day |
| D | Alternative layout | 在不改变已确认科学关系的前提下重组构图 |
| E | Visual variant | 保留内容和拓扑，尝试不同配色与图形语言 |

5 张必须来自 5 次分别调用，不能让 ImageGen 一次生成五联图。在 5 张原图都存在后，可以用本地代码组装仅供比较的 contact sheet。

## 人工控制点

1. **澄清**：你纠正会改变科学含义或画面结果的歧义；这是短对话，不是额外 approval gate。
2. **候选决定**：你查看 A–E，可以选择、定向修改、组合两张的布局/配色，或全部重生。
3. **最终检查**：你审查精确文字、公式、箭头方向、原生可编辑对象和目标软件中的外观。

自动 validation 可以检查文件解析、对象、标签、连接和格式结构，但不能证明科学正确，也不会自动写入最终批准。PDF 只是 export/preview，不称为可编辑源。

## 当前 Deep Image Prior 示例

[`examples/deep_image_prior/`](examples/deep_image_prior/README.md) 收录了：

- 你原创的手绘 Deep Image Prior 原理草图，不是根据某张 paper figure 仿画；
- 本次对话得到的简短澄清 brief；
- 5 次分别调用 Codex 内置 ImageGen 产生的 A–E 原图；
- 候选文件哈希、调用记录和本地组装的对比图。

你最初选择了 **D 的布局 + C 的视觉风格**，随后否决了该版本；只使用 **候选 C** 的第一版原生重绘也因视觉质感不足而被否决。后续 hybrid 虽保留了两个图像区域，但公式发生非等比拉伸，而且没有真正执行完整的分区映射。旧版本均作为决策历史保留，不再称为 current。当前 canonical 指针是 [`editable_delivery_c_fidelity_v2/`](examples/deep_image_prior/editable_delivery_c_fidelity_v2/README.md)：它绑定候选 C 的哈希和 8 区 map，保留两个无重采样、可替换 raster atom，并用原生/vector 对象重建网络层、框、两条 synthetic curve、箭头、标签和 9 个公式。

公式以 [`source/equations.tex`](examples/deep_image_prior/editable_delivery_c_fidelity_v2/source/equations.tex) 为权威源，并由本地 LaTeX 渲染为保持原始宽高比的 vector equation objects。PPTX 和 SVG 中的结构对象可分别编辑；SVG 的两个 raster atom 使用 `delivery/svg/assets/` 下的相对 sidecar，必须与 `master.svg` 一起移动。两个 image atom 可整体替换，但不可逐像素编辑，也不是科学证据。draw.io 仅是 experimental topology view：官方 CLI 当前会把主要彩色区域渲染成黑块，并把 9 个公式显示为 raw LaTeX，因此不能作为视觉保真证据。PDF 只是 export/preview。

当前 v0.1 已有一条绑定 frozen artifact-manifest SHA-256 的独立人工 visual approval；它不会随 rebuild 自动继承，也不包含 scientific、Science Day 或 public-release approval。后三项仍为 pending。自动 validation 只检查可编程的文件与连接结构，不能代替这些决定。完整边界见 [v0.1 reference case](examples/deep_image_prior/reference_case_v0_1.md)。

## 离线开发者 fixture（非默认用户路径）

从 repository root、Python 3.11+ 环境运行；输出路径必须位于仓库外且尚不存在：

```bash
python -m pip install -r requirements.txt
python scripts/run_synthetic_demo.py \
  --mode core \
  --output-dir /tmp/sketch-figure-core-demo-01
```

如果系统默认 `python`/`python3` 低于 3.11，请在上述命令中统一换成已安装的 `python3.11` 或更新版本。

预期结果是 `status: INCOMPLETE` 和 `stage: incomplete_core_only`。这是一个不执行 AI 的 checked-in deterministic adapter/test fixture，用来证明部分可编辑重建和格式验证，不代表默认 ImageGen 用户路径。完整现场讲解见 [Science Day demo guide](docs/science-day-demo.md)。

## 旧版 V3 离线适配器参考（非默认）

以下内容保留用于回归测试和显式请求的 legacy contract-driven run。其 `scientific_truth.json`、blueprint、deterministic skeleton 和旧版 Gate 1/2 不是当前 Quick Start 的用户步骤。

## 运行时产物

- `scientific_truth.json`：稳定 ID、实体实例、关系、计数、符号、源文件哈希和禁止暗示；
- `candidate_blueprint.json`：region、port、edge、rule ID、geometry 和 fingerprint；
- `*_skeleton.svg/png`：从 blueprint 确定性渲染的结构参考；
- `generation_brief.md`：350–500 词，只保留视觉消息、参考图角色、阻塞性视觉规则、art direction 和文字白名单；
- `review_result.json`：把规则分成 image-level blocking、acceptable raster imperfection、must-fix in SVG、caption-only；
- `selected_candidate_map.json`：只迁移构图和艺术方向，明确废弃生成文字/公式/连接线；
- `svg_reconstruction_spec.json`：语义 SVG 的稳定对象、端口、连接和验证要求；
- `validation_rules.json`：各阶段共享的 `rule_id` 注册表。

## 执行流程

### 1. 建立并确认科学真值

使用 `prompts/00_scientific_figure_brief.md`。先处理来源冲突；不得用旧图或生成图覆盖当前方程。主论文方法图通常使用 `story-first` profile，最多展示两组关键方程；其余方程仍完整保存在 truth 或 caption 角色中。

### 2. 编译蓝图、规则和短 brief

每个 blueprint 用稳定 semantic IDs 绑定 truth instances，并显式记录 source port、target port、relation ID 和 rule IDs。编译器必须在生成前拒绝不完整引用、brief 越界和重复 fingerprint。

### 3. 渲染确定性拓扑骨架

从同一 scene 同时输出 SVG 与 PNG。骨架负责 major regions、cardinality、grouping、stage order、rough placement、fan-out/fan-in 和关键 transition；它不负责最终配色、装饰、长公式或 connector 美化。

### 4. 在外部生成并注册 PNG（可选）

若 operator 使用图像生成，每个候选应对应一次独立调用，只附带它自己的 skeleton 作为结构参考；可选第二张图只能作为 style-only reference。不得使用 contact sheet、上一候选上下文或相互竞争的结构参考。Repository runner 只注册 exact PNG bytes、SHA-256、call ID 和 Gate 1 bindings；它不调用 generator，也不独立验证 generator identity。

### 5. 做宏观审查并停止过度修 raster

PNG 必须通过 stage order、major counts、grouping、source/target relation、fan-out/fan-in 和禁止暗示等阻塞规则。精确文字、公式、索引、派生位置、port、端点和 routing 统一在 SVG 阶段重建。

每个 blueprint 最多一次全局 regeneration；每个候选最多一次只影响样式的局部编辑。不得用局部 raster edit 修数量、阶段顺序、分组、source/target、fan-in/fan-out、centroid、公式、connector rewiring 或 backward multiplicity。同一拓扑错误重复出现时，修改 blueprint/skeleton 或淘汰候选。

### 6. 确定性重建语义 SVG

使用 `prompts/02_selected_proposal_to_svg.md`：

- truth 决定内容、数量、符号和关系；
- blueprint 决定语义拓扑与几何；
- selected-candidate map 只决定 palette、stroke character、corner language、whitespace rhythm 和 glyph appearance。

最终 SVG 必须有可解析 XML、唯一稳定 ID、语义 group、live text、显式 port、带 source/target/relation/rule metadata 的独立 connector、全局 style tokens，且不得把整张 PNG 包进 SVG。默认不使用 raster atoms；若你明确要求复用已选候选图的某个无标签区域，必须另外记录候选哈希、精确 bbox、review-draft-only decision 和 asset manifest，且最终 publication/scientific approval 继续留空。

### 7. 结构检查并由研究者决定

使用 `scripts/validate_figure_artifacts.py`、`scripts/validate_semantic_svg.py` 或 full delivery 的 `scripts/validate_delivery.py`。同时进行最终尺寸、灰度、公式隐藏和科学审阅。`VERIFIED` 仅表示可编程结构检查通过，不等于科学正确，也不会自动创建 Gate 3 approval。

## 订阅边界与文件保护

- 所有历史 run 只读保留；新实验使用新的 dated run directory。
- 不凭空声称改进。没有跨案例数据、人工修正时长和最终选择时，结论只能是 preliminary 或 `INSUFFICIENT_EVIDENCE`。
- Canonical source 是 truth、blueprint、规则和 semantic SVG，不是生成 PNG，也不是 Figma 回导文件。
- Figma-ready SVG 的状态是 `IMPORT_READY_UNVERIFIED`，不能声称真实 Figma import 已验证。
- PDF 是 vector export/preview，`semantic_editability=false`；canonical semantic JSON、LaTeX、SVG 与 PPTX 是主要可编辑源。只有通过对应 official-render 检查的 draw.io 才能扩大格式声明；当前 fidelity-v2 draw.io 仅是 experimental structural view。
- 未经目标应用和科研内容审阅，不得把产物描述为 publication-ready 或 production-ready。
