# Start here / 从这里开始

## 这个项目是什么

这是一个由研究者控制的 Codex workflow：先把手绘科学草图转成五个视觉候选，再把研究者批准的一个精确候选重建成可编辑科学图。

**想直接开始？** 克隆或下载仓库，在 Codex 中打开项目文件夹，附上草图并调用 `$sketch-to-scientific-figure`。回答必要问题、选定候选、批准分区方案后，再检查生成的可编辑图。新结果应保存到仓库外；不要覆盖参考案例。如果 Skill 没有出现在列表里，请让 Codex 读取 [SKILL.md](.agents/skills/sketch-to-scientific-figure/SKILL.md) 并按其链接的 prompts 执行。

> 手绘草图 → 聚焦澄清 → 5 次分别调用内置 ImageGen → 研究者批准一个精确候选 → 分区映射 → 原生可编辑 SVG/PPTX → experimental draw.io 结构视图 → PDF 预览 → 自动结构检查 → 研究者最终决定

**Codex 提方案，重建工具做转换，自动检查验证可编程约束，科研人员做决定。**

v0.1 提供可复用 workflow 和一个经过验证的 Deep Image Prior 参考案例；它不是适用于任意草图的通用转换器，也不保证跨草图重建效果。

**直接查看参考成果：** [SVG 文件夹](examples/deep_image_prior/editable_delivery_c_fidelity_v2/delivery/svg/) · [PowerPoint](examples/deep_image_prior/editable_delivery_c_fidelity_v2/delivery/pptx/figure.pptx) · [PDF 预览](examples/deep_image_prior/editable_delivery_c_fidelity_v2/delivery/pdf/publication.pdf) · [draw.io 实验性结构视图](examples/deep_image_prior/editable_delivery_c_fidelity_v2/delivery/drawio/figure.drawio)

SVG 的 `master.svg` 必须与旁边的 `assets/` 文件夹一起保存，否则会缺少两个图像区域。请克隆或下载仓库，或运行下面的离线 replay 获取完整文件包；PPTX 可单独打开。这些是冻结参考成果，不是对你的草图新生成的结果。

## 路径一：用于你自己的草图

1. 在支持内置图像生成的 Codex App 会话中打开本仓库并附上草图。
2. 说明必须精确保留的标签、公式、箭头含义，以及任何敏感或未发表内容边界。
3. 调用：

```text
$sketch-to-scientific-figure
```

4. Codex 先检查草图和已有对话，每轮只问 1–3 个真正会改变结果的问题，通常不超过两轮。
5. 信息足够后，Codex 使用同一张草图和同一份短 brief，分别调用五次内置 ImageGen，得到 A–E 五张原图。
6. 研究者批准其中一个精确候选，或要求生成新版本。
7. Codex 建立候选哈希绑定的 region map；研究者检查科学拓扑和 raster 例外后明确批准。
8. 重建工具生成 SVG、PPTX、draw.io 和 PDF，并执行结构检查。
9. 研究者分别决定视觉效果、科学内容、演示使用和公开发布是否可以接受。

五次调用是五个分开的生成事件；项目不声称它们具有统计独立性。默认 live 路径使用 Codex 内置 ImageGen，不要求 `OPENAI_API_KEY`，也不是由仓库 Python 代码调用图像模型。内置生成能力是否可用取决于 Codex 环境。

### 固定候选方向

| 槽位 | 方向 | 目的 |
|---|---|---|
| A | Faithful | 保留草图的主要布局和识别特征 |
| B | Publication | 紧凑、克制、适合论文图幅 |
| C | Presentation | 强化层级和远距离可读性 |
| D | Alternative layout | 在不改变科学关系的前提下重组构图 |
| E | Visual variant | 尝试不同配色和图形语言 |

如果你说 `Revise C`，Codex 应生成并登记一个新的 C 版本，再让你检查。如果你说“用 C 的布局和 A 的颜色”，这只是新图的生成 brief，不是可以直接进入重建的 combination approval：必须先生成一张新的候选图，再批准其精确文件和哈希。若科学 brief 或整体方向发生实质变化，应开启新一轮 A–E。

## 路径二：离线重放参考案例

从 repository root 使用 Python 3.11+：

```bash
python -m pip install -r requirements.txt
python scripts/replay_reference_case.py replay \
  --output-dir /tmp/sketch-figure-reference-v0-1
python scripts/replay_reference_case.py validate \
  --run-dir /tmp/sketch-figure-reference-v0-1
python scripts/replay_reference_case.py status \
  --run-dir /tmp/sketch-figure-reference-v0-1
```

如果默认 `python` 低于 3.11，请把四条命令统一换成可用的 `python3.11` 或更新版本。replay 输出目录必须位于仓库外且尚不存在。

这条路径只验证和复制冻结证据，不调用 ImageGen、网络或远程服务，也不会生成新的人工批准。预期 workflow stage 为 `VISUAL_APPROVED`。checked-in governance fields 保留冻结时的状态；annotated `v0.1.0` tag 另行记录该发布 tree 的 owner attestation。

可选的 fidelity-v2 **重新构建**与 replay 不同：除 Python 依赖外，还需要 Codex bundled runtime 中的 `@oai/artifact-tool`、Node.js、LaTeX/dvisvgm、LibreOffice 和 Poppler。脱离该 bundled runtime 的独立安装方案尚未验证；缺少这些工具时使用 replay，不要把复制冻结成果称为重新生成。具体要求见 [runtime requirements](docs/runtime_requirements.md)。

## Deep Image Prior 参考案例

[`examples/deep_image_prior/`](examples/deep_image_prior/README.md) 包含：

- repository author 原创的手绘原理草图；
- 简短澄清 brief；
- 五次分别调用 Codex 内置 ImageGen 得到的 A–E 原图；
- 候选哈希、generation-event records 和本地生成的 contact sheet；
- Candidate C 的哈希绑定选择；
- 研究者批准的八区 region map；
- canonical [`editable_delivery_c_fidelity_v2/`](examples/deep_image_prior/editable_delivery_c_fidelity_v2/README.md)；
- 结构验证和 hash-bound visual approval。

Fidelity v2 只保留两个经批准、可独立替换的 synthetic raster atoms。网络层、框、曲线、箭头、标签和九个公式使用 native/vector objects 重建。公式的权威源是 LaTeX；输出中的 vector equation object 可缩放和整体编辑，但不等于语义层面的可编辑 LaTeX。

SVG 和 PPTX 是本案例的主要可编辑输出。draw.io 包含可编辑 graph cells 和 directed edges，但其官方渲染仍有已知视觉缺陷，所以只称 experimental structural view。PDF 只称 export/preview。

## 人工与自动化的边界

| 环节 | Codex / 工具做什么 | 研究者决定什么 |
|---|---|---|
| 澄清 | 找出会改变结果的歧义 | 科学含义、精确符号和边界 |
| 候选 | 提出五个视觉方向 | 批准哪一个精确候选，或要求新版本 |
| Region map | 草拟分区、对象和转换方式 | 拓扑是否正确、哪些 raster 例外可接受 |
| 重建 | 生成原生对象和格式 | 视觉表达是否忠实且可用 |
| Validation | 检查文件、对象、哈希、路径和基础拓扑 | 科学是否正确、是否可用于演示或公开发布 |

自动 validation 不能证明科学正确，也不会自动创建视觉、科学内容、用途或公开发布批准。

## 更多信息

- [English README](README.md)
- [Technical reference](docs/technical_reference.md)
- [Reference-case evidence](examples/deep_image_prior/reference_case_v0_1.md)
- [Asset provenance and licensing boundaries](ASSETS.md)

旧版 V2/V3 contract-driven workflow 保存在不可变的 `v0.1.0` 发布历史中，不是当前 Skill 或 Quick Start 的执行说明。
