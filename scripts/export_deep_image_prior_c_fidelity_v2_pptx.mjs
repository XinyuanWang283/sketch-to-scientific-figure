#!/usr/bin/env node
/** Export Candidate C fidelity v2 as editable PowerPoint objects. */

import crypto from "node:crypto";
import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { pathToFileURL } from "node:url";

const SLIDE_WIDTH = 1672;
const SLIDE_HEIGHT = 941;
const DEFAULT_NATIVE_REGION_SHAPE_MINIMUM = 40;
const REQUIRED_FLAGS = ["--spec", "--equation-dir", "--asset-dir", "--output-dir"];
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
    "  export_deep_image_prior_c_fidelity_v2_pptx.mjs \\",
    "    --spec <semantic-figure.json> \\",
    "    --equation-dir <equation-svg-directory> \\",
    "    --asset-dir <source-asset-directory> \\",
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

function clampOpacity(value) {
  if (value === undefined || value === null) return 1;
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) throw new Error(`Opacity must be numeric, received ${String(value)}`);
  return Math.max(0, Math.min(1, numeric > 1 ? numeric / 100 : numeric));
}

function colorWithOpacity(color, opacity) {
  const alpha = clampOpacity(opacity);
  if (alpha >= 0.999999) return color;
  if (typeof color === "string") {
    if (color === "none" || color === "transparent") return color;
    const match = color.match(/^(.*)\/(\d+(?:\.\d+)?)$/);
    const base = match ? match[1] : color;
    const existing = match ? clampOpacity(Number(match[2])) : 1;
    return `${base}/${Math.round(existing * alpha * 10000) / 100}`;
  }
  if (color && typeof color === "object") {
    const existing = clampOpacity(color.transform?.opacity);
    return {
      ...color,
      transform: {
        ...(color.transform || {}),
        opacity: existing * alpha,
      },
    };
  }
  throw new Error("Fill color must be a supported color string or color object");
}

function normalizeGradientOffset(value, allOffsets) {
  const numeric = Number(value);
  if (!Number.isFinite(numeric) || numeric < 0) throw new Error(`Invalid gradient stop offset: ${String(value)}`);
  const maximum = Math.max(...allOffsets.map(Number));
  if (maximum <= 1) return Math.round(numeric * 100000);
  if (maximum <= 100) return Math.round(numeric * 1000);
  return Math.min(100000, Math.round(numeric));
}

function normalizeFill(fill, opacity = 1) {
  const alpha = clampOpacity(opacity);
  if (fill === undefined || fill === null) return "none";
  if (typeof fill === "string") return colorWithOpacity(fill, alpha);
  if (typeof fill !== "object") throw new Error("Fill must be a string or object");
  if (fill.type === "none") return { type: "none" };
  if (fill.type === "solid") {
    return {
      ...fill,
      color: colorWithOpacity(fill.color, alpha),
    };
  }

  const type = fill.type || fill.kind;
  const isGradient = type === "gradient" || type === "linear_gradient" || type === "linearGradient";
  if (!isGradient) throw new Error(`Unsupported native shape fill type: ${String(type || "<missing>")}`);
  if (!Array.isArray(fill.stops) || fill.stops.length < 2) {
    throw new Error("Gradient fills require at least two stops");
  }
  const rawOffsets = fill.stops.map((stop) => stop.offset);
  return {
    type: "gradient",
    gradientKind: fill.gradientKind || fill.gradient_kind || "linear",
    angleDeg: Number(fill.angleDeg ?? fill.angle_deg ?? fill.angle ?? 0),
    stops: fill.stops.map((stop) => ({
      offset: normalizeGradientOffset(stop.offset, rawOffsets),
      color: colorWithOpacity(stop.color, alpha * clampOpacity(stop.opacity)),
    })),
  };
}

function fillUsesGradient(fill) {
  if (typeof fill === "string") return /^(?:linear|radial)\(/i.test(fill);
  const type = fill?.type || fill?.kind;
  return type === "gradient" || type === "linear_gradient" || type === "linearGradient";
}

function colorUsesAlpha(color) {
  if (typeof color === "string") return /\/\d+(?:\.\d+)?$/.test(color);
  if (!color || typeof color !== "object") return false;
  const opacity = color.transform?.opacity;
  return opacity !== undefined && clampOpacity(opacity) < 0.999999;
}

function fillUsesAlpha(fill, opacity) {
  if (clampOpacity(opacity) < 0.999999) return true;
  if (typeof fill === "string") return colorUsesAlpha(fill);
  if (!fill || typeof fill !== "object") return false;
  if (fill.type === "solid") return colorUsesAlpha(fill.color);
  return Array.isArray(fill.stops) && fill.stops.some((stop) => (
    clampOpacity(stop.opacity) < 0.999999 || colorUsesAlpha(stop.color)
  ));
}

function assertPoints(points, id) {
  if (!Array.isArray(points) || points.length < 2) throw new Error(`${id} must have at least two points`);
  for (const point of points) {
    if (!Array.isArray(point) || point.length !== 2 || point.some((value) => !Number.isFinite(Number(value)))) {
      throw new Error(`${id} contains an invalid point`);
    }
  }
}

function customPathConfig(id, points, { fill = "none", line, close = false } = {}) {
  assertPoints(points, id);
  const xs = points.map(([x]) => Number(x));
  const ys = points.map(([, y]) => Number(y));
  const left = Math.min(...xs);
  const top = Math.min(...ys);
  const width = Math.max(1, Math.max(...xs) - left);
  const height = Math.max(1, Math.max(...ys) - top);
  const commands = [
    { moveTo: { x: xs[0] - left, y: ys[0] - top } },
    ...points.slice(1).map(([x, y]) => ({ lineTo: { x: Number(x) - left, y: Number(y) - top } })),
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
  const width = Number(shape.stroke_width || 0);
  const none = !shape.stroke || shape.stroke === "none" || width <= 0;
  return {
    style: shape.dash?.length ? "dashed" : "solid",
    fill: none ? "none" : normalizeFill(shape.stroke || fallback, shape.stroke_opacity ?? shape.opacity ?? 1),
    width: none ? 0.1 : width,
  };
}

function recordPaint(counts, fill, opacity) {
  if (fillUsesGradient(fill)) counts.native_gradient_fills += 1;
  if (fillUsesAlpha(fill, opacity)) counts.native_alpha_fills += 1;
}

function addNativeShape(slide, shape, counts) {
  const fill = shape.type === "polygon" ? normalizeFill(shape.fill, shape.fill_opacity ?? shape.opacity ?? 1) : "none";
  if (shape.type === "polygon" || shape.type === "polyline" || shape.type === "path") {
    if (shape.type === "polygon") recordPaint(counts, shape.fill, shape.fill_opacity ?? shape.opacity ?? 1);
    return slide.shapes.add(customPathConfig(shape.id, shape.points, {
      fill,
      line: lineStyle(shape),
      close: shape.type === "polygon",
    }));
  }
  if (shape.type !== "ellipse" && shape.type !== "rect" && shape.type !== "roundRect") {
    throw new Error(`Unsupported native shape type: ${String(shape.type)}`);
  }
  recordPaint(counts, shape.fill, shape.fill_opacity ?? shape.opacity ?? 1);
  const config = {
    geometry: shape.type,
    name: shape.id,
    position: shape.position,
    fill: normalizeFill(shape.fill, shape.fill_opacity ?? shape.opacity ?? 1),
    line: lineStyle(shape),
  };
  if (shape.type === "roundRect" && shape.radius !== undefined) config.borderRadius = shape.radius;
  return slide.shapes.add(config);
}

function addFrameFill(slide, frame, counts) {
  recordPaint(counts, frame.fill, frame.fill_opacity ?? frame.opacity ?? 1);
  const config = {
    geometry: frame.geometry,
    name: `${frame.id}-fill`,
    position: frame.position,
    fill: normalizeFill(frame.fill, frame.fill_opacity ?? frame.opacity ?? 1),
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
      fill: normalizeFill(frame.stroke, frame.stroke_opacity ?? frame.opacity ?? 1),
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

async function resolveFileWithin(rootDir, relativePath, label) {
  if (path.isAbsolute(relativePath)) throw new Error(`${label} must use a relative path`);
  const root = await fs.realpath(rootDir);
  const filePath = await fs.realpath(path.resolve(root, relativePath));
  if (!filePath.startsWith(`${root}${path.sep}`)) throw new Error(`${label} escapes its package directory`);
  await assertFile(filePath, label);
  return filePath;
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

async function readApprovedImage(module, assetDir) {
  const filePath = await resolveFileWithin(assetDir, module.asset, `${module.id} exact raster atom`);
  const bytes = await fs.readFile(filePath);
  if (sha256(bytes) !== module.sha256) throw new Error(`${module.id} asset hash mismatch`);
  if (!bytes.subarray(1, 4).equals(Buffer.from("PNG"))) throw new Error(`${module.id} must be a PNG`);
  return bytes;
}

function nativeShapeMinimum(spec) {
  const value = Number(
    spec.editability_contract?.native_region_shape_minimum
      ?? DEFAULT_NATIVE_REGION_SHAPE_MINIMUM,
  );
  if (!Number.isInteger(value) || value < 1) {
    throw new Error("editability_contract.native_region_shape_minimum must be a positive integer");
  }
  return value;
}

async function buildPresentation(spec, equationDir, assetDir, artifactModule) {
  const { Presentation, PresentationFile } = artifactModule;
  if (spec.canvas?.width !== SLIDE_WIDTH || spec.canvas?.height !== SLIDE_HEIGHT) {
    throw new Error(`Canvas must be exactly ${SLIDE_WIDTH}x${SLIDE_HEIGHT}`);
  }
  if (spec.editability_contract?.approved_replaceable_raster_atom_count !== 2) {
    throw new Error("Exactly two approved replaceable raster atoms are required");
  }
  if (spec.image_modules?.length !== 2) throw new Error("spec.image_modules must contain exactly two entries");
  const minimumNativeShapes = nativeShapeMinimum(spec);
  const presentation = Presentation.create({ slideSize: { width: SLIDE_WIDTH, height: SLIDE_HEIGHT } });
  const slide = presentation.slides.add();
  slide.background.fill = normalizeFill(spec.canvas.background, spec.canvas.opacity ?? 1);
  const counts = {
    native_connector_shafts: 0,
    native_arrowheads: 0,
    native_frame_fills: 0,
    native_frame_outlines: 0,
    native_region_shapes: 0,
    native_labels: 0,
    native_gradient_fills: 0,
    native_alpha_fills: 0,
    equation_svg_objects: 0,
    independent_raster_atoms: 0,
    whole_slide_rasters: 0,
  };

  // Keep all frame backgrounds below the connector layer. The measurement
  // panel encloses two residual arrows, so a later panel fill would hide them.
  for (const frame of spec.frames) {
    addFrameFill(slide, frame, counts);
    counts.native_frame_fills += 1;
  }

  for (const connector of spec.connectors) {
    slide.shapes.add(customPathConfig(`${connector.id}-shaft`, connector.shaft_points, {
      fill: "none",
      line: {
        style: connector.dash?.length ? "dashed" : "solid",
        fill: normalizeFill(connector.stroke, connector.stroke_opacity ?? connector.opacity ?? 1),
        width: connector.stroke_width,
      },
    }));
    counts.native_connector_shafts += 1;
    recordPaint(counts, connector.stroke, connector.fill_opacity ?? connector.opacity ?? 1);
    slide.shapes.add(customPathConfig(`${connector.id}-arrowhead`, connector.arrowhead_points, {
      fill: normalizeFill(connector.stroke, connector.fill_opacity ?? connector.opacity ?? 1),
      line: {
        style: "solid",
        fill: normalizeFill(connector.stroke, connector.stroke_opacity ?? connector.opacity ?? 1),
        width: 0.1,
      },
      close: true,
    }));
    counts.native_arrowheads += 1;
  }
  if (!counts.native_connector_shafts || counts.native_connector_shafts !== counts.native_arrowheads) {
    throw new Error("Every native connector shaft must have one explicit native arrowhead");
  }

  const rasterRecords = [];
  for (const module of spec.image_modules) {
    if (!module.replaceable || module.pixel_editable !== false || module.scientific_status !== "synthetic_visual_only") {
      throw new Error(`${module.id} does not satisfy the replaceable synthetic-visual contract`);
    }
    const bytes = await readApprovedImage(module, assetDir);
    const image = slide.images.add({
      blob: bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength),
      contentType: "image/png",
      alt: `[${module.id}] exact replaceable synthetic visual atom; not scientific evidence and not pixel-editable`,
      fit: "contain",
      position: module.position,
    });
    try { image.name = module.id; } catch (_) { /* alt text retains the stable identity */ }
    counts.independent_raster_atoms += 1;
    rasterRecords.push({
      id: module.id,
      source: module.asset,
      sha256: module.sha256,
      position: module.position,
      replaceable: true,
      pixel_editable: false,
      scientific_status: "synthetic_visual_only",
    });
  }

  for (const shapes of Object.values(spec.regions || {})) {
    if (!Array.isArray(shapes)) throw new Error("Every regions entry must be an array of native shapes");
    for (const shape of shapes) {
      addNativeShape(slide, shape, counts);
      counts.native_region_shapes += 1;
    }
  }
  if (counts.native_region_shapes < minimumNativeShapes) {
    throw new Error(
      `At least ${minimumNativeShapes} native region shapes are required; found ${counts.native_region_shapes}`,
    );
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
      color: normalizeFill(label.color, label.opacity ?? 1),
      alignment: "center",
    };
    counts.native_labels += 1;
  }

  const equationRecords = [];
  for (const equation of spec.equation_objects) {
    const filePath = await resolveFileWithin(
      equationDir,
      path.basename(equation.asset),
      `${equation.id} vector equation`,
    );
    const bytes = await fs.readFile(filePath);
    if (sha256(bytes) !== equation.sha256) {
      throw new Error(`${equation.id} vector equation hash mismatch`);
    }
    const svgText = bytes.toString("utf8");
    if (!/<svg\b/i.test(svgText) || /<image\b/i.test(svgText)) {
      throw new Error(`${equation.id} must be a complete raster-free SVG`);
    }
    const intrinsic = equation.intrinsic_viewbox;
    const target = equation.target_position;
    const intrinsicRatio = intrinsic[2] / intrinsic[3];
    const targetRatio = target.width / target.height;
    if (Math.abs(targetRatio - intrinsicRatio) / intrinsicRatio > 0.005) {
      throw new Error(`${equation.id} target box does not preserve intrinsic aspect ratio`);
    }
    const image = slide.images.add({
      blob: bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength),
      contentType: "image/svg+xml",
      alt: `[${equation.id}] vector equation. LaTeX: ${equation.latex_source}`,
      fit: "contain",
      position: target,
    });
    try { image.name = equation.id; } catch (_) { /* alt text retains identity */ }
    counts.equation_svg_objects += 1;
    equationRecords.push({
      id: equation.id,
      equation_id: equation.equation_id,
      source: `source/math/${path.basename(equation.asset)}`,
      sha256: sha256(bytes),
      latex_source: equation.latex_source,
      intrinsic_viewbox: intrinsic,
      target_position: target,
    });
  }
  if (counts.equation_svg_objects !== 9) throw new Error("Exactly nine vector equation objects are required");

  const notes = [
    "Candidate C fidelity-v2 editable delivery.",
    "Canonical source: source/semantic_figure.json",
    "Selected-candidate map: source/selected_candidate_map.json",
    "Asset manifest: source/asset_manifest.json",
    "The Candidate C visual reference is not embedded as a whole-slide image.",
    "Two exact image atoms are independent, replaceable picture shapes; they are not pixel-editable or scientific evidence.",
    "Frames, generator layers, plots, connectors, explicit arrowheads, and labels are native editable PowerPoint objects.",
    "Gradient and alpha styling remain native PowerPoint shape styling; equation artwork remains raster-free SVG objects.",
    "Visual-reference reconstruction and automated checks do not establish scientific correctness or final researcher approval.",
    "[Sources]",
    "- source/selected_candidate_map.json — hash-bound visual direction map.",
    "- source/asset_manifest.json — exact crop provenance and release policy.",
    ...rasterRecords.map((item) => `- source/${item.source} — exact replaceable synthetic visual atom ${item.sha256}.`),
    ...equationRecords.map((item) => `- ${item.source} — locally rendered raster-free vector equation.`),
  ];
  notes.forEach((line, index) => assertNoLocalPath(line, `speaker-note line ${index + 1}`));
  slide.speakerNotes.textFrame.setText(notes);
  slide.speakerNotes.setVisible(false);
  return {
    presentation,
    slide,
    counts,
    rasterRecords,
    equationRecords,
    minimumNativeShapes,
    PresentationFile,
  };
}

async function exportArtifacts(spec, specBytes, equationDir, assetDir, artifactModule, outputDir) {
  const stagingDir = await fs.mkdtemp(path.join(os.tmpdir(), "c-fidelity-v2-pptx-"));
  try {
    const built = await buildPresentation(spec, equationDir, assetDir, artifactModule);
    const {
      presentation,
      slide,
      counts,
      rasterRecords,
      equationRecords,
      minimumNativeShapes,
      PresentationFile,
    } = built;
    await writeBlob(path.join(stagingDir, "slide-01.png"), await presentation.export({ slide, format: "png", scale: 1 }));
    const layout = await slide.export({ format: "layout" });
    await fs.writeFile(path.join(stagingDir, "slide-01.layout.json"), await layout.text());
    const inspection = await presentation.inspect({ kind: "slide,textbox,shape,image,notes", maxChars: 250000 });
    await fs.writeFile(path.join(stagingDir, "artifact_tool_inspect.ndjson"), inspection.ndjson || "");
    const pptx = await PresentationFile.exportPptx(presentation);
    await pptx.save(path.join(stagingDir, "figure.pptx"));
    const report = {
      schema_version: "1.1",
      status: "AUTHORED_PENDING_RENDER_AND_HUMAN_REVIEW",
      canonical_source: "source/semantic_figure.json",
      canonical_source_sha256: sha256(specBytes),
      canvas: spec.canvas,
      slide_count: 1,
      object_counts: counts,
      raster_atoms: rasterRecords,
      equation_modules: equationRecords,
      constraints: {
        selected_candidate_map_present: Boolean(spec.selected_candidate_map),
        whole_candidate_pixels_embedded: false,
        approved_raster_atom_count: 2,
        native_region_shape_minimum: minimumNativeShapes,
        native_region_shape_minimum_met: counts.native_region_shapes >= minimumNativeShapes,
        native_connectors_and_explicit_arrowheads: true,
        native_gradient_and_alpha_styling_supported: true,
        equation_aspect_ratio_preserved: true,
        automated_scientific_approval: false,
        final_scientific_approval: null,
      },
      outputs: {
        pptx: "figure.pptx",
        preview: "slide-01.png",
        layout: "slide-01.layout.json",
        inspection: "artifact_tool_inspect.ndjson",
        report: "pptx_artifact_report.json",
      },
      verification_boundary: (
        "The exporter checks object structure, approved atom provenance, equation vector form, and declared editability constraints. "
        + "Independent render comparison and researcher judgment remain required; this report does not validate scientific correctness."
      ),
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
    assetDir: path.resolve(args["asset-dir"]),
    outputDir: path.resolve(args["output-dir"]),
  };
  await assertFile(paths.spec, "--spec");
  await assertDirectory(paths.equationDir, "--equation-dir");
  await assertDirectory(paths.assetDir, "--asset-dir");
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
  await exportArtifacts(spec, specBytes, paths.equationDir, paths.assetDir, artifactModule, paths.outputDir);
}

main().catch((error) => {
  process.stderr.write(`${error?.stack || String(error)}\n`);
  process.exitCode = 1;
});
