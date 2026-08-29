#!/usr/bin/env node
/** Export the region-first Candidate-C revision as native PowerPoint objects. */

import crypto from "node:crypto";
import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { pathToFileURL } from "node:url";

const SLIDE_WIDTH = 1672;
const SLIDE_HEIGHT = 941;
const REQUIRED_FLAGS = ["--spec", "--equation-dir", "--output-dir"];
const OUTPUT_NAMES = [
  "slide-01.png",
  "slide-01.layout.json",
  "artifact_tool_inspect.ndjson",
  "figure.pptx",
  "pptx_artifact_report.json",
];

function usage() {
  return [
    "Usage:",
    "  export_deep_image_prior_c_segmented_native_pptx.mjs \\",
    "    --spec <semantic-figure.json> \\",
    "    --equation-dir <equation-svg-directory> \\",
    "    --output-dir <new-or-empty-output-directory>",
  ].join("\n");
}

function parseArgs(argv) {
  if (argv.includes("--help")) {
    process.stdout.write(`${usage()}\n`);
    return null;
  }
  const values = new Map();
  for (let index = 0; index < argv.length; index += 2) {
    const flag = argv[index];
    const value = argv[index + 1];
    if (!REQUIRED_FLAGS.includes(flag)) throw new Error(`Unknown argument: ${flag || "<empty>"}\n${usage()}`);
    if (!value || value.startsWith("--")) throw new Error(`Missing value for ${flag}\n${usage()}`);
    if (values.has(flag)) throw new Error(`Duplicate argument: ${flag}`);
    values.set(flag, value);
  }
  for (const flag of REQUIRED_FLAGS) {
    if (!values.has(flag)) throw new Error(`Missing required argument: ${flag}\n${usage()}`);
  }
  return Object.fromEntries(REQUIRED_FLAGS.map((flag) => [flag.slice(2), values.get(flag)]));
}

function assertNoLocalPath(value, label) {
  const text = String(value);
  const patterns = [
    /(?:^|[\s"'])\/Users\//i,
    /(?:^|[\s"'])\/private\//i,
    /(?:^|[\s"'])\/home\//i,
    /(?:^|[\s"'])[A-Z]:\\Users\\/i,
    /file:\/\//i,
  ];
  if (patterns.some((pattern) => pattern.test(text))) throw new Error(`${label} contains a local path`);
  return text;
}

function sha256(bytes) {
  return crypto.createHash("sha256").update(bytes).digest("hex");
}

function customPathConfig(id, points, { fill = "none", line, close = false } = {}) {
  const xs = points.map(([x]) => x);
  const ys = points.map(([, y]) => y);
  const left = Math.min(...xs);
  const top = Math.min(...ys);
  const width = Math.max(1, Math.max(...xs) - left);
  const height = Math.max(1, Math.max(...ys) - top);
  const commands = [
    { moveTo: { x: points[0][0] - left, y: points[0][1] - top } },
    ...points.slice(1).map(([x, y]) => ({ lineTo: { x: x - left, y: y - top } })),
  ];
  if (close) commands.push({ close: {} });
  return {
    geometry: "custom",
    name: id,
    position: { left, top, width, height },
    fill,
    line,
    customPaths: [{ width, height, commands }],
  };
}

function lineStyle(shape, fallback = "#0D2F6E") {
  const none = !shape.stroke || shape.stroke === "none" || Number(shape.stroke_width || 0) <= 0;
  return {
    style: shape.dash?.length ? "dashed" : "solid",
    fill: none ? "none" : shape.stroke || fallback,
    width: none ? 0.1 : Number(shape.stroke_width),
  };
}

function addNativeShape(slide, shape) {
  if (shape.type === "polygon" || shape.type === "polyline") {
    return slide.shapes.add(customPathConfig(shape.id, shape.points, {
      fill: shape.type === "polygon" ? shape.fill : "none",
      line: lineStyle(shape),
      close: shape.type === "polygon",
    }));
  }
  const geometry = shape.type === "ellipse" ? "ellipse" : "rect";
  return slide.shapes.add({
    geometry,
    name: shape.id,
    position: shape.position,
    fill: shape.fill,
    line: lineStyle(shape),
  });
}

function addFrameFill(slide, frame) {
  const config = {
    geometry: frame.geometry,
    name: `${frame.id}-fill`,
    position: frame.position,
    fill: frame.fill,
    line: { style: "solid", fill: "none", width: 0.1 },
  };
  if (frame.geometry === "roundRect") config.borderRadius = frame.radius;
  return slide.shapes.add(config);
}

function addFrameOutline(slide, frame) {
  const config = {
    geometry: frame.geometry,
    name: frame.id,
    position: frame.position,
    fill: "none",
    line: {
      style: frame.dash?.length ? "dashed" : "solid",
      fill: frame.stroke,
      width: frame.stroke_width,
    },
  };
  if (frame.geometry === "roundRect") config.borderRadius = frame.radius;
  return slide.shapes.add(config);
}

async function writeBlob(filePath, blob) {
  await fs.writeFile(filePath, new Uint8Array(await blob.arrayBuffer()));
}

async function assertFile(filePath, label) {
  const stat = await fs.stat(filePath).catch(() => null);
  if (!stat?.isFile()) throw new Error(`${label} must be a file`);
}

async function assertDirectory(filePath, label) {
  const stat = await fs.stat(filePath).catch(() => null);
  if (!stat?.isDirectory()) throw new Error(`${label} must be a directory`);
}

async function assertOutputsAvailable(outputDir) {
  await fs.mkdir(outputDir, { recursive: true });
  const occupied = [];
  for (const name of OUTPUT_NAMES) {
    try {
      await fs.access(path.join(outputDir, name));
      occupied.push(name);
    } catch (error) {
      if (error?.code !== "ENOENT") throw error;
    }
  }
  if (occupied.length) throw new Error(`Refusing to overwrite existing output(s): ${occupied.join(", ")}`);
}

async function buildPresentation(spec, equationDir, artifactModule) {
  const { Presentation, PresentationFile } = artifactModule;
  if (spec.canvas?.width !== SLIDE_WIDTH || spec.canvas?.height !== SLIDE_HEIGHT) {
    throw new Error(`Canvas must be exactly ${SLIDE_WIDTH}x${SLIDE_HEIGHT}`);
  }
  if (spec.editability_contract?.candidate_or_crop_raster_count !== 0) {
    throw new Error("Candidate or crop raster modules are forbidden in this exporter");
  }
  const presentation = Presentation.create({ slideSize: { width: SLIDE_WIDTH, height: SLIDE_HEIGHT } });
  const slide = presentation.slides.add();
  slide.background.fill = spec.canvas.background;
  const counts = {
    native_connector_shafts: 0,
    native_arrowheads: 0,
    native_frame_fills: 0,
    native_frame_outlines: 0,
    native_region_shapes: 0,
    native_labels: 0,
    equation_svg_objects: 0,
    candidate_or_crop_rasters: 0,
  };

  // Connectors are placed before nodes so they remain behind all surfaces.
  for (const connector of spec.connectors) {
    slide.shapes.add(customPathConfig(`${connector.id}-shaft`, connector.shaft_points, {
      fill: "none",
      line: {
        style: connector.dash?.length ? "dashed" : "solid",
        fill: connector.stroke,
        width: connector.stroke_width,
      },
    }));
    counts.native_connector_shafts += 1;
    slide.shapes.add(customPathConfig(`${connector.id}-arrowhead`, connector.arrowhead_points, {
      fill: connector.stroke,
      line: { style: "solid", fill: connector.stroke, width: 0.1 },
      close: true,
    }));
    counts.native_arrowheads += 1;
  }

  for (const frame of spec.frames) {
    addFrameFill(slide, frame);
    counts.native_frame_fills += 1;
  }
  for (const shapes of Object.values(spec.regions)) {
    for (const shape of shapes) {
      addNativeShape(slide, shape);
      counts.native_region_shapes += 1;
    }
  }
  for (const frame of spec.frames) {
    addFrameOutline(slide, frame);
    counts.native_frame_outlines += 1;
  }
  for (const label of spec.labels) {
    const textbox = slide.shapes.add({
      geometry: "textbox",
      name: label.id,
      position: label.position,
      fill: "none",
      line: { style: "solid", fill: "none", width: 0.1 },
    });
    textbox.text = label.text;
    textbox.text.style = {
      fontSize: label.font_size,
      fontFamily: label.font_family,
      color: label.color,
      alignment: "center",
    };
    counts.native_labels += 1;
  }

  const equationRecords = [];
  for (const equation of spec.equation_objects) {
    const filePath = path.join(equationDir, path.basename(equation.asset));
    await assertFile(filePath, `${equation.id} vector equation`);
    const bytes = await fs.readFile(filePath);
    const text = bytes.toString("utf8");
    if (!/<svg\b/i.test(text) || /<image\b/i.test(text)) {
      throw new Error(`${equation.id} must be a complete raster-free SVG`);
    }
    const image = slide.images.add({
      blob: bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength),
      contentType: "image/svg+xml",
      alt: `[${equation.id}] vector equation. LaTeX: ${equation.latex_source}`,
      fit: "contain",
      position: equation.target_position,
    });
    try { image.name = equation.id; } catch (_) { /* alt text retains identity */ }
    counts.equation_svg_objects += 1;
    equationRecords.push({
      id: equation.id,
      equation_id: equation.equation_id,
      source: `source/math/${path.basename(equation.asset)}`,
      sha256: sha256(bytes),
      latex_source: equation.latex_source,
      intrinsic_viewbox: equation.intrinsic_viewbox,
      target_position: equation.target_position,
    });
  }

  const notes = [
    "Candidate C region-first native editable review revision.",
    "Canonical source: source/semantic_figure.json",
    "Selected-candidate map: source/selected_candidate_map.json",
    "Candidate crops are reference-only and are not embedded in this slide.",
    "All scientific frames, regions, plots, connectors, arrowheads, and labels are native PowerPoint objects.",
    "Equations are locally rendered vector SVG objects whose target boxes preserve their intrinsic viewBox ratio.",
    "Automated checks do not establish scientific correctness; final researcher approval remains pending.",
    "[Sources]",
    "- source/selected_candidate_map.json — selected visual direction map.",
    ...equationRecords.map((item) => `- ${item.source} — locally rendered vector equation.`),
  ];
  notes.forEach((line, index) => assertNoLocalPath(line, `speaker-note line ${index + 1}`));
  slide.speakerNotes.textFrame.setText(notes);
  slide.speakerNotes.setVisible(false);
  return { presentation, slide, counts, equationRecords, PresentationFile };
}

async function exportArtifacts(spec, specBytes, equationDir, artifactModule, outputDir) {
  const stagingDir = await fs.mkdtemp(path.join(os.tmpdir(), "segmented-native-pptx-"));
  try {
    const { presentation, slide, counts, equationRecords, PresentationFile } = await buildPresentation(spec, equationDir, artifactModule);
    await writeBlob(path.join(stagingDir, "slide-01.png"), await presentation.export({ slide, format: "png", scale: 1 }));
    const layout = await slide.export({ format: "layout" });
    await fs.writeFile(path.join(stagingDir, "slide-01.layout.json"), await layout.text());
    const inspection = await presentation.inspect({ kind: "slide,textbox,shape,image,notes", maxChars: 150000 });
    await fs.writeFile(path.join(stagingDir, "artifact_tool_inspect.ndjson"), inspection.ndjson || "");
    const pptx = await PresentationFile.exportPptx(presentation);
    await pptx.save(path.join(stagingDir, "figure.pptx"));
    const report = {
      schema_version: "1.0",
      status: "AUTHORED_PENDING_VISUAL_QA",
      canonical_source: "source/semantic_figure.json",
      canonical_source_sha256: sha256(specBytes),
      canvas: spec.canvas,
      slide_count: 1,
      object_counts: counts,
      equation_modules: equationRecords,
      constraints: {
        selected_candidate_map_present: true,
        selected_candidate_pixels_embedded: false,
        native_regions: true,
        native_connectors_and_small_arrowheads: true,
        equation_aspect_ratio_preserved: true,
        scientific_approval: false,
      },
      outputs: {
        pptx: "figure.pptx",
        preview: "slide-01.png",
        layout: "slide-01.layout.json",
        inspection: "artifact_tool_inspect.ndjson",
        report: "pptx_artifact_report.json",
      },
      verification_boundary: "Artifact authored; visual QA, overflow testing, and final scientific approval remain separate checks.",
    };
    const reportText = `${JSON.stringify(report, null, 2)}\n`;
    assertNoLocalPath(reportText, "portable PPTX report");
    await fs.writeFile(path.join(stagingDir, "pptx_artifact_report.json"), reportText);
    for (const name of OUTPUT_NAMES) {
      await fs.copyFile(path.join(stagingDir, name), path.join(outputDir, name));
    }
  } finally {
    await fs.rm(stagingDir, { recursive: true, force: true });
  }
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  if (!args) return;
  const paths = {
    spec: path.resolve(args.spec),
    equationDir: path.resolve(args["equation-dir"]),
    outputDir: path.resolve(args["output-dir"]),
  };
  await assertFile(paths.spec, "--spec");
  await assertDirectory(paths.equationDir, "--equation-dir");
  await assertOutputsAvailable(paths.outputDir);
  const specBytes = await fs.readFile(paths.spec);
  const spec = JSON.parse(specBytes.toString("utf8"));
  const moduleRoot = process.env.RUNTIME_NODE_MODULES;
  if (!moduleRoot || !path.isAbsolute(moduleRoot)) {
    throw new Error("RUNTIME_NODE_MODULES must be set to the bundled absolute module directory");
  }
  const artifactPath = path.join(moduleRoot, "@oai", "artifact-tool", "dist", "artifact_tool.mjs");
  await assertFile(artifactPath, "bundled @oai/artifact-tool module");
  const artifactModule = await import(pathToFileURL(artifactPath).href);
  await exportArtifacts(spec, specBytes, paths.equationDir, artifactModule, paths.outputDir);
}

main().catch((error) => {
  process.stderr.write(`${error?.stack || String(error)}\n`);
  process.exitCode = 1;
});
