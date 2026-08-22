# 从这里开始

## 项目用途

这个 repository-scoped Skill 把科研草图和权威方法材料转成可验证、可编辑的论文图：

> 科学真值结构化 → 编译候选蓝图 → 确定性拓扑骨架 → 内置图像生成 PNG → 人工选择宏观构图 → 契约驱动语义 SVG → 可执行验证

科学含义只来自当前权威方程、明确方法文字和已确认的科学约束。草图提供待核对的空间意图；只有经过科学核对并写入 truth/blueprint 的特征才成为约束。生成 PNG 只提供构图、层级、配色、glyph 外观、留白和节奏，不提供可靠的公式、索引、数量、端点或箭头语义。

## 最短用法

在 Codex 中打开本仓库，上传草图和方法材料，然后调用：

```text
$sketch-to-scientific-figure
```

图像生成阶段只使用 ChatGPT/Codex 订阅内置能力：不调用 Image API，不请求 API key，不增加 Web App、数据库、OCR、SAM 或自动描摹。本地 Python 检查和完整的多格式输出仍需要 [runtime requirements](docs/runtime_requirements.md) 中列出的工具。

## 三次人工确认

1. **科学真值**：确认一句话信息、实体、关系、计数、阶段顺序、方程角色、禁止暗示和未决歧义。
2. **PNG 宏观构图与配色**：从通过 image-level blocking review 的候选中选择 layout/palette。该选择不批准生成图中的文字、公式、索引、centroid 或 connector。
3. **最终图签字**：语义 SVG 通过可执行 validator 和最终尺寸视觉检查后，研究者确认科学内容与表达。

Guided discovery 只是补齐信息，每轮只问一个会改变结果的问题；它不是额外确认节点。

## 候选数量

| `PROPOSAL_MODE` | 数量 | 使用条件 |
|---|---:|---|
| `focused-one` | 1 | 拓扑固定，只需一个视觉处理方向 |
| `directed-three` | 3 | 正常默认；比较 sketch-faithful、mechanism-dominant、compact editorial |
| `exploratory-five` | 5 | 信息层级确实未定，且五个 fingerprint 全部通过 lint |

多候选必须先通过 layout fingerprint 检查。角色名、颜色、字体、圆角和框样式不算实质差异。

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

### 4. 独立生成 PNG

每个候选执行一次内置图像生成调用，只附带它自己的 skeleton 作为结构参考；可选第二张图只能作为 style-only reference。不得使用 contact sheet、上一候选上下文或相互竞争的结构参考。

### 5. 做宏观审查并停止过度修 raster

PNG 必须通过 stage order、major counts、grouping、source/target relation、fan-out/fan-in 和禁止暗示等阻塞规则。精确文字、公式、索引、派生位置、port、端点和 routing 统一在 SVG 阶段重建。

每个 blueprint 最多一次全局 regeneration；每个候选最多一次只影响样式的局部编辑。不得用局部 raster edit 修数量、阶段顺序、分组、source/target、fan-in/fan-out、centroid、公式、connector rewiring 或 backward multiplicity。同一拓扑错误重复出现时，修改 blueprint/skeleton 或淘汰候选。

### 6. 确定性重建语义 SVG

使用 `prompts/02_selected_proposal_to_svg.md`：

- truth 决定内容、数量、符号和关系；
- blueprint 决定语义拓扑与几何；
- selected-candidate map 只决定 palette、stroke character、corner language、whitespace rhythm 和 glyph appearance。

最终 SVG 必须有可解析 XML、唯一稳定 ID、语义 group、live text、显式 port、带 source/target/relation/rule metadata 的独立 connector、全局 style tokens，且不得把整张 PNG 包进 SVG。默认不使用 raster atoms；任何例外都必须在 asset manifest 中说明。

### 7. 验证并签字

使用 `scripts/validate_figure_artifacts.py` 和 `scripts/validate_semantic_svg.py`。同时进行最终尺寸、灰度、公式隐藏和科学审阅。自动 validator 是检查点，不替代研究者判断。

## 订阅边界与文件保护

- 所有历史 run 只读保留；新实验使用新的 dated run directory。
- 不凭空声称改进。没有跨案例数据、人工修正时长和最终选择时，结论只能是 preliminary 或 `INSUFFICIENT_EVIDENCE`。
- Canonical source 是 truth、blueprint、规则和 semantic SVG，不是生成 PNG，也不是 Figma 回导文件。
