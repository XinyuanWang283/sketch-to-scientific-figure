#!/usr/bin/env node
/**
 * Export the candidate-C high-fidelity hybrid figure as one editable PPTX slide.
 *
 * Two bounded photographic modules (noise and reconstruction) remain raster
 * PNGs. Frames, network faces, plots, labels, connectors, and arrowheads are
 * native PowerPoint objects. Equations are embedded as vector SVGs whose alt
 * text and speaker notes retain the authoritative LaTeX source.
 */

import crypto from "node:crypto";
import fs from "node:fs/promises";
import path from "node:path";
import { pathToFileURL } from "node:url";

const SLIDE_WIDTH = 1672;
const SLIDE_HEIGHT = 941;
const OUTPUT_NAMES = [
  "slide-01.png",
  "slide-01.layout.json",
  "artifact_tool_inspect.ndjson",
  "figure.pptx",
  "pptx_artifact_report.json",
];
const REQUIRED_FLAGS = ["--spec", "--asset-dir", "--equation-dir", "--output-dir"];
const PNG_SIGNATURE = Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]);

function usage() {
  return [
    "Usage:",
    "  export_deep_image_prior_c_hybrid_pptx.mjs \\",
    "    --spec <hybrid-spec.json> \\",
    "    --asset-dir <png-assets> \\",
    "    --equation-dir <equation-svgs> \\",
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
    if (!REQUIRED_FLAGS.includes(flag)) {
      throw new Error(`Unknown argument: ${flag || "<empty>"}\n${usage()}`);
    }
    if (!value || value.startsWith("--")) {
      throw new Error(`Missing value for ${flag}\n${usage()}`);
    }
    if (values.has(flag)) throw new Error(`Duplicate argument: ${flag}`);
    values.set(flag, value);
  }
  for (const flag of REQUIRED_FLAGS) {
    if (!values.has(flag)) throw new Error(`Missing required argument: ${flag}\n${usage()}`);
  }
  return Object.fromEntries(REQUIRED_FLAGS.map((flag) => [flag.slice(2), values.get(flag)]));
}

function isRecord(value) {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

function assertRecord(value, label) {
  if (!isRecord(value)) throw new Error(`${label} must be an object`);
  return value;
}

function assertArray(value, label, { min = 0, exact = null } = {}) {
  if (!Array.isArray(value)) throw new Error(`${label} must be an array`);
  if (exact !== null && value.length !== exact) {
    throw new Error(`${label} must contain exactly ${exact} items`);
  }
  if (value.length < min) throw new Error(`${label} must contain at least ${min} item(s)`);
  return value;
}

function finiteNumber(value, label, { min = -Infinity, max = Infinity } = {}) {
  const number = Number(value);
  if (!Number.isFinite(number) || number < min || number > max) {
    throw new Error(`${label} must be a finite number in [${min}, ${max}]`);
  }
  return number;
}

function nonEmptyString(value, label) {
  if (typeof value !== "string" || !value.trim()) throw new Error(`${label} must be a non-empty string`);
  return value.trim();
}

function assertNoLocalPath(value, label) {
  const text = String(value);
  const forbidden = [
    /(?:^|[\s"'])\/Users\//i,
    /(?:^|[\s"'])\/home\//i,
    /(?:^|[\s"'])\/private\//i,
    /(?:^|[\s"'])[A-Z]:\\Users\\/i,
    /file:\/\//i,
  ];
  if (forbidden.some((pattern) => pattern.test(text))) {
    throw new Error(`${label} contains a local filesystem path`);
  }
  return text;
}

function portableLabel(value, fallback, label) {
  const candidate = assertNoLocalPath(value ?? fallback, label).replaceAll("\\", "/");
  if (
    candidate.startsWith("/")
    || candidate.includes("../")
    || candidate === ".."
    || /^[A-Za-z]:/.test(candidate)
  ) {
    throw new Error(`${label} must be a portable relative label`);
  }
  return nonEmptyString(candidate, label);
}

function sha256(bytes) {
  return crypto.createHash("sha256").update(bytes).digest("hex");
}

function validateId(value, label) {
  const id = nonEmptyString(value, label);
  if (!/^[A-Za-z][A-Za-z0-9_.-]*$/.test(id)) {
    throw new Error(`${label} must start with a letter and contain only letters, digits, ., _, or -`);
  }
  return id;
}

function registerId(id, seenIds, label) {
  if (seenIds.has(id)) throw new Error(`${label} duplicates stable object id "${id}"`);
  seenIds.add(id);
}

function positionOf(item, label, canvas) {
  const source = isRecord(item.position) ? item.position : item;
  const left = finiteNumber(source.left ?? source.x, `${label}.position.left`, { min: 0 });
  const top = finiteNumber(source.top ?? source.y, `${label}.position.top`, { min: 0 });
  const width = finiteNumber(source.width, `${label}.position.width`, { min: 1 });
  const height = finiteNumber(source.height, `${label}.position.height`, { min: 1 });
  if (left + width > canvas.width + 0.01 || top + height > canvas.height + 0.01) {
    throw new Error(`${label} extends beyond the ${canvas.width}x${canvas.height} canvas`);
  }
  return { left, top, width, height };
}

function cropOf(value, label) {
  const crop = assertRecord(value, `${label}.crop`);
  const result = Object.fromEntries(
    ["left", "top", "right", "bottom"].map((side) => [
      side,
      finiteNumber(crop[side], `${label}.crop.${side}`, { min: 0, max: 0.95 }),
    ]),
  );
  if (result.left + result.right >= 1 || result.top + result.bottom >= 1) {
    throw new Error(`${label}.crop removes the complete image`);
  }
  return result;
}

function assertPaint(value, label, fallback) {
  const paint = value ?? fallback;
  if (isRecord(paint)) {
    if (paint.type !== "gradient") throw new Error(`${label} object must be a gradient fill`);
    const stops = assertArray(paint.stops, `${label}.stops`, { min: 2 }).map((stop, index) => {
      const entry = assertRecord(stop, `${label}.stops[${index}]`);
      return {
        offset: finiteNumber(entry.offset, `${label}.stops[${index}].offset`, { min: 0, max: 100000 }),
        color: assertPaint(entry.color, `${label}.stops[${index}].color`, "#FFFFFF"),
      };
    });
    return {
      type: "gradient",
      gradientKind: paint.gradientKind === "path" ? "path" : "linear",
      angleDeg: finiteNumber(paint.angleDeg ?? 0, `${label}.angleDeg`, { min: -360, max: 360 }),
      stops,
    };
  }
  const string = nonEmptyString(paint, label);
  const safe = /^(?:none|transparent|white|black|#[0-9A-Fa-f]{3,8}|(?:linear|radial)\([^;{}]+\))$/;
  if (!safe.test(string)) throw new Error(`${label} uses an unsupported paint value: ${string}`);
  return string;
}

function lineOf(item, label, defaults = {}) {
  const line = isRecord(item.line) ? item.line : {};
  const rawStyle = line.style ?? item.line_style ?? item.dash ?? defaults.style ?? "solid";
  const style = typeof rawStyle === "boolean"
    ? (rawStyle ? "dashed" : "solid")
    : (/^[\d\s.,-]+$/.test(String(rawStyle)) ? "dashed" : rawStyle);
  const allowedStyles = new Set(["solid", "dashed", "dotted", "dash-dot", "dash-dot-dot"]);
  if (!allowedStyles.has(style)) throw new Error(`${label}.line.style is unsupported: ${style}`);
  return {
    style,
    fill: assertPaint(line.fill ?? line.color ?? item.stroke, `${label}.line.fill`, defaults.fill ?? "#0B2A64"),
    width: finiteNumber(line.width ?? line.weight ?? item.stroke_width ?? defaults.width ?? 2, `${label}.line.width`, { min: 0.1, max: 30 }),
  };
}

function shadowOf(value, fallback = "shadow-sm") {
  const shadow = value ?? fallback;
  if (typeof shadow !== "string") throw new Error("shadow must be a string");
  if (/^shadow-(?:none|sm|md|lg|xl|2xl)$/.test(shadow) || shadow === "shadow") return shadow;
  if (/^-?\d+(?:\.\d+)?px\s+-?\d+(?:\.\d+)?px\s+\d+(?:\.\d+)?px\s+#[0-9A-Fa-f]{6}\/(?:\d|[1-9]\d|100)$/.test(shadow)) {
    return shadow;
  }
  throw new Error(`Unsupported shadow value: ${shadow}`);
}

function pointsOf(value, label, canvas, { min = 2 } = {}) {
  const source = isRecord(value) ? value.points : value;
  return assertArray(source, `${label}.points`, { min }).map((point, index) => {
    const pair = assertArray(point, `${label}.points[${index}]`, { exact: 2 });
    const x = finiteNumber(pair[0], `${label}.points[${index}][0]`, { min: 0, max: canvas.width });
    const y = finiteNumber(pair[1], `${label}.points[${index}][1]`, { min: 0, max: canvas.height });
    return [x, y];
  });
}

function customPathConfig(id, points, { fill = "none", line, close = false, shadow = undefined } = {}) {
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
    ...(shadow ? { shadow } : {}),
    customPaths: [{ width, height, commands }],
  };
}

function arrowheadPoints(points, size, label) {
  const target = points.at(-1);
  let previousIndex = points.length - 2;
  while (
    previousIndex >= 0
    && points[previousIndex][0] === target[0]
    && points[previousIndex][1] === target[1]
  ) previousIndex -= 1;
  if (previousIndex < 0) throw new Error(`${label} has no non-zero final segment`);
  const previous = points[previousIndex];
  const angle = Math.atan2(target[1] - previous[1], target[0] - previous[0]);
  const spread = 0.5;
  return [
    target,
    [target[0] - size * Math.cos(angle - spread), target[1] - size * Math.sin(angle - spread)],
    [target[0] - size * Math.cos(angle + spread), target[1] - size * Math.sin(angle + spread)],
  ];
}

function roleOfImage(item) {
  const role = String(item.role ?? item.id).toLowerCase();
  if (role.includes("noise") || role === "z") return "noise";
  if (role.includes("reconstruction") || role.includes("estimate") || role.includes("xhat") || role === "x-hat") {
    return "reconstruction";
  }
  return role;
}

async function safeFileUnder(rootDirectory, relativePath, label, extension) {
  const relative = nonEmptyString(relativePath, label).replaceAll("\\", "/");
  if (relative.startsWith("/") || relative === ".." || relative.includes("../") || /^[A-Za-z]:/.test(relative)) {
    throw new Error(`${label} must be a relative path inside its declared directory`);
  }
  if (path.extname(relative).toLowerCase() !== extension) {
    throw new Error(`${label} must reference a ${extension} file`);
  }
  const root = await fs.realpath(rootDirectory);
  const candidate = await fs.realpath(path.resolve(root, relative));
  if (candidate !== root && !candidate.startsWith(`${root}${path.sep}`)) {
    throw new Error(`${label} resolves outside its declared directory`);
  }
  const stat = await fs.stat(candidate);
  if (!stat.isFile()) throw new Error(`${label} is not a regular file`);
  return { absolute: candidate, relative };
}

function portableAssetPath(prefix, relative) {
  return `${prefix}/${relative.replaceAll("\\", "/")}`.replace(/\/+/g, "/");
}

async function validateAndLoadSpec(spec, paths) {
  assertRecord(spec, "spec");
  const canvasSource = assertRecord(spec.canvas, "spec.canvas");
  const canvas = {
    width: finiteNumber(canvasSource.width, "spec.canvas.width", { min: 1 }),
    height: finiteNumber(canvasSource.height, "spec.canvas.height", { min: 1 }),
    background: assertPaint(canvasSource.background, "spec.canvas.background", "#FFFFFF"),
  };
  if (canvas.width !== SLIDE_WIDTH || canvas.height !== SLIDE_HEIGHT) {
    throw new Error(`Candidate C hybrid canvas must be exactly ${SLIDE_WIDTH}x${SLIDE_HEIGHT}`);
  }

  const sourceLabel = portableLabel(spec.source_label, `source/${path.basename(paths.spec)}`, "spec.source_label");
  const assetPrefix = portableLabel(spec.asset_label_prefix, "assets", "spec.asset_label_prefix");
  const equationPrefix = portableLabel(spec.equation_label_prefix, "equations", "spec.equation_label_prefix");
  const seenIds = new Set();

  const imageRoles = new Set();
  const imageModules = [];
  for (const [index, raw] of assertArray(spec.image_modules, "spec.image_modules", { exact: 2 }).entries()) {
    const item = assertRecord(raw, `spec.image_modules[${index}]`);
    const id = validateId(item.id, `spec.image_modules[${index}].id`);
    registerId(id, seenIds, `spec.image_modules[${index}]`);
    const role = roleOfImage(item);
    if (!new Set(["noise", "reconstruction"]).has(role)) {
      throw new Error(`${id} must declare role "noise" or "reconstruction"`);
    }
    if (imageRoles.has(role)) throw new Error(`spec.image_modules contains duplicate role "${role}"`);
    imageRoles.add(role);
    const position = positionOf(item, `spec.image_modules[${index}]`, canvas);
    if (
      position.left <= 1
      && position.top <= 1
      && position.width >= canvas.width - 2
      && position.height >= canvas.height - 2
    ) {
      throw new Error(`${id} would create a forbidden full-canvas raster`);
    }
    const asset = await safeFileUnder(paths.assetDir, item.asset, `${id}.asset`, ".png");
    const bytes = await fs.readFile(asset.absolute);
    if (bytes.length < PNG_SIGNATURE.length || !bytes.subarray(0, PNG_SIGNATURE.length).equals(PNG_SIGNATURE)) {
      throw new Error(`${id}.asset is not a valid PNG byte stream`);
    }
    imageModules.push({
      id,
      role,
      asset,
      bytes,
      position,
      // The source files are already publication-cropped atoms. Retain an
      // explicit PowerPoint crop record even when no additional inset is used.
      crop: cropOf(item.crop ?? { left: 0, top: 0, right: 0, bottom: 0 }, `spec.image_modules[${index}]`),
      fit: item.fit === "contain" ? "contain" : "cover",
      geometry: item.geometry ?? "roundRect",
      radius: finiteNumber(item.radius ?? item.border_radius ?? 15, `${id}.radius`, { min: 0, max: 120 }),
      alt: assertNoLocalPath(item.alt ?? `${role} image module`, `${id}.alt`),
      portable: portableAssetPath(assetPrefix, asset.relative),
    });
  }
  if (!imageRoles.has("noise") || !imageRoles.has("reconstruction")) {
    throw new Error("spec.image_modules must contain one noise and one reconstruction PNG module");
  }
  for (const item of imageModules) {
    if (!["rect", "roundRect", "ellipse"].includes(item.geometry)) {
      throw new Error(`${item.id}.geometry must be rect, roundRect, or ellipse`);
    }
  }

  const frames = assertArray(spec.frames, "spec.frames", { min: 1 }).map((raw, index) => {
    const item = assertRecord(raw, `spec.frames[${index}]`);
    const id = validateId(item.id, `spec.frames[${index}].id`);
    registerId(id, seenIds, `spec.frames[${index}]`);
    const geometry = item.geometry ?? "roundRect";
    if (!["rect", "roundRect", "ellipse"].includes(geometry)) {
      throw new Error(`${id}.geometry must be rect, roundRect, or ellipse`);
    }
    const radius = finiteNumber(
      item.radius ?? item.border_radius ?? item.rx ?? (geometry === "ellipse" ? 0 : 18),
      `${id}.radius`,
      { min: 0, max: 160 },
    );
    return {
      id,
      geometry,
      position: positionOf(item, `spec.frames[${index}]`, canvas),
      fill: assertPaint(item.fill, `${id}.fill`, "linear(90deg, #FFFFFF 0%, #F6F4FB 100%)"),
      line: lineOf(item, id, { fill: "#233B73", width: 2.5 }),
      radius,
      shadow: shadowOf(item.shadow, "shadow-none"),
    };
  });

  const networkLayers = assertArray(spec.network_layers, "spec.network_layers", { min: 1 }).map((raw, index) => {
    const item = assertRecord(raw, `spec.network_layers[${index}]`);
    const id = validateId(item.id, `spec.network_layers[${index}].id`);
    registerId(id, seenIds, `spec.network_layers[${index}]`);
    const parts = {};
    for (const [partName, fallback] of [
      ["top", "linear(90deg, #ECEAF8 0%, #AAA4D4 100%)"],
      ["side", "linear(90deg, #4B477D 0%, #7771A5 100%)"],
      ["face", "linear(90deg, #8D88BE 0%, #5D588E 100%)"],
    ]) {
      const rawPart = item[partName];
      if (!rawPart) throw new Error(`${id}.${partName} is required`);
      const objectPart = isRecord(rawPart) ? rawPart : { points: rawPart };
      const partId = `${id}-${partName}`;
      registerId(partId, seenIds, `${id}.${partName}`);
      parts[partName] = {
        id: partId,
        points: pointsOf(objectPart, `${id}.${partName}`, canvas, { min: 3 }),
        fill: assertPaint(objectPart.fill ?? item[`${partName}_fill`], `${id}.${partName}.fill`, fallback),
        line: lineOf(objectPart, `${id}.${partName}`, { fill: "#423D75", width: 1.4 }),
        shadow: partName === "face" ? shadowOf(objectPart.shadow ?? item.shadow, "shadow-sm") : undefined,
      };
    }
    return { id, parts };
  });

  const plotPaths = [];
  for (const [plotIndex, raw] of assertArray(spec.plot_paths, "spec.plot_paths", { min: 1 }).entries()) {
    const plot = assertRecord(raw, `spec.plot_paths[${plotIndex}]`);
    const plotId = validateId(plot.id, `spec.plot_paths[${plotIndex}].id`);
    const grouped = Array.isArray(plot.grid_lines) || Array.isArray(plot.curves);
    if (grouped) registerId(plotId, seenIds, `spec.plot_paths[${plotIndex}]`);
    const groups = grouped
      ? [["grid", plot.grid_lines ?? []], ["curve", plot.curves ?? []]]
      : [[plot.role ?? "curve", [plot]]];
    for (const [role, entries] of groups) {
      for (const [entryIndex, entryRaw] of assertArray(entries, `${plotId}.${role}`).entries()) {
        const entry = isRecord(entryRaw) ? entryRaw : { points: entryRaw };
        const id = validateId(
          grouped ? (entry.id ?? `${plotId}-${role}-${entryIndex + 1}`) : plotId,
          `${plotId}.${role}[${entryIndex}].id`,
        );
        registerId(id, seenIds, `${plotId}.${role}[${entryIndex}]`);
        plotPaths.push({
          id,
          role,
          points: pointsOf(entry, `${plotId}.${role}[${entryIndex}]`, canvas, { min: 2 }),
          line: lineOf(entry, `${plotId}.${role}[${entryIndex}]`, {
            fill: role === "grid" ? "#C7CEDB" : "#0A2E6E",
            width: role === "grid" ? 1 : 3,
            style: role === "grid" ? "dashed" : "solid",
          }),
        });
      }
    }
  }

  const connectors = assertArray(spec.connectors, "spec.connectors", { min: 1 }).map((raw, index) => {
    const item = assertRecord(raw, `spec.connectors[${index}]`);
    const id = validateId(item.id, `spec.connectors[${index}].id`);
    registerId(id, seenIds, `spec.connectors[${index}]`);
    const points = pointsOf(item, `spec.connectors[${index}]`, canvas, { min: 2 });
    const headValue = item.head ?? "triangle";
    const hasHead = headValue !== "none" && headValue !== false;
    const headId = `${id}-arrowhead`;
    if (hasHead) registerId(headId, seenIds, `${id}.head`);
    return {
      id,
      points,
      line: lineOf(item, id, { fill: "#0A2E6E", width: 3 }),
      hasHead,
      headId,
      headSize: finiteNumber(isRecord(headValue) ? headValue.size ?? 16 : item.head_size ?? 16, `${id}.head_size`, { min: 4, max: 60 }),
    };
  });

  const labelsSource = spec.labels ?? spec.text_objects;
  const labels = assertArray(labelsSource, "spec.labels", { min: 1 }).map((raw, index) => {
    const item = assertRecord(raw, `spec.labels[${index}]`);
    const id = validateId(item.id, `spec.labels[${index}].id`);
    registerId(id, seenIds, `spec.labels[${index}]`);
    const style = isRecord(item.style) ? item.style : {};
    return {
      id,
      text: assertNoLocalPath(nonEmptyString(item.text, `${id}.text`), `${id}.text`),
      position: positionOf(item, `spec.labels[${index}]`, canvas),
      fontSize: finiteNumber(style.font_size ?? style.fontSize ?? item.font_size ?? 28, `${id}.font_size`, { min: 10, max: 120 }),
      fontFamily: nonEmptyString(style.font_family ?? style.fontFamily ?? item.font_family ?? "Arial", `${id}.font_family`),
      color: assertPaint(style.color ?? item.color, `${id}.color`, "#0A2E6E"),
      bold: Boolean(style.bold ?? item.bold ?? false),
      italic: Boolean(style.italic ?? item.italic ?? false),
      alignment: ["left", "center", "right"].includes(style.alignment ?? item.alignment ?? item.align)
        ? (style.alignment ?? item.alignment ?? item.align)
        : "center",
    };
  });

  const equations = [];
  for (const [index, raw] of assertArray(spec.equation_objects, "spec.equation_objects", { min: 1 }).entries()) {
    const item = assertRecord(raw, `spec.equation_objects[${index}]`);
    const id = validateId(item.id, `spec.equation_objects[${index}].id`);
    registerId(id, seenIds, `spec.equation_objects[${index}]`);
    const equationId = validateId(item.equation_id ?? id, `${id}.equation_id`);
    const asset = await safeFileUnder(paths.equationDir, item.asset ?? `${equationId}.svg`, `${id}.asset`, ".svg");
    const bytes = await fs.readFile(asset.absolute);
    const svgText = bytes.toString("utf8");
    if (!/<svg\b/i.test(svgText) || !/<\/svg>/i.test(svgText)) throw new Error(`${id}.asset is not a complete SVG document`);
    if (/<image\b/i.test(svgText)) throw new Error(`${id}.asset embeds a raster image; vector equation SVG required`);
    const latex = assertNoLocalPath(nonEmptyString(item.latex_source ?? item.latex, `${id}.latex_source`), `${id}.latex_source`);
    equations.push({
      id,
      equationId,
      asset,
      bytes,
      latex,
      position: positionOf(item, `spec.equation_objects[${index}]`, canvas),
      alt: assertNoLocalPath(`${item.alt ?? `Equation ${equationId}`}. LaTeX: ${latex}`, `${id}.alt`),
      portable: portableAssetPath(equationPrefix, asset.relative),
    });
  }

  return {
    canvas,
    sourceLabel,
    imageModules,
    frames,
    networkLayers,
    plotPaths,
    connectors,
    labels,
    equations,
  };
}

async function readJson(filePath) {
  const bytes = await fs.readFile(filePath);
  try {
    return { value: JSON.parse(bytes.toString("utf8")), bytes };
  } catch (error) {
    throw new Error(`Invalid JSON in --spec: ${error.message}`);
  }
}

async function assertInputPath(filePath, label, kind) {
  const stat = await fs.stat(filePath).catch(() => null);
  if (!stat) throw new Error(`${label} does not exist`);
  if (kind === "file" && !stat.isFile()) throw new Error(`${label} must be a file`);
  if (kind === "directory" && !stat.isDirectory()) throw new Error(`${label} must be a directory`);
}

async function assertOutputsAvailable(outputDir) {
  const stat = await fs.stat(outputDir).catch(() => null);
  if (!stat) return;
  if (!stat.isDirectory()) throw new Error("--output-dir must be a directory");
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

async function writeBlob(filePath, blob) {
  await fs.writeFile(filePath, new Uint8Array(await blob.arrayBuffer()));
}

function setStableImageName(image, id) {
  try {
    image.name = id;
  } catch (_) {
    // Some artifact-tool versions expose stable image identity through alt text
    // only. The canonical id remains the leading token in that alt text.
  }
}

async function buildPresentation(model, artifactModule) {
  const { Presentation, PresentationFile } = artifactModule;
  const presentation = Presentation.create({
    slideSize: { width: model.canvas.width, height: model.canvas.height },
  });
  const slide = presentation.slides.add();
  slide.background.fill = model.canvas.background;
  const counts = {
    native_connector_paths: 0,
    native_arrowheads: 0,
    native_frames: 0,
    native_network_faces: 0,
    native_plot_paths: 0,
    native_labels: 0,
    cropped_png_modules: 0,
    equation_svg_images: 0,
  };

  // Connector paths are deliberately authored first so they remain behind
  // all node surfaces. Arrowheads are native custom polygons, not raster art.
  for (const connector of model.connectors) {
    slide.shapes.add(customPathConfig(connector.id, connector.points, {
      fill: "none",
      line: connector.line,
    }));
    counts.native_connector_paths += 1;
    if (connector.hasHead) {
      const headPoints = arrowheadPoints(connector.points, connector.headSize, connector.id);
      slide.shapes.add(customPathConfig(connector.headId, headPoints, {
        fill: connector.line.fill,
        line: { style: "solid", fill: connector.line.fill, width: 0.5 },
        close: true,
      }));
      counts.native_arrowheads += 1;
    }
  }

  for (const frame of model.frames) {
    const config = {
      geometry: frame.geometry,
      name: frame.id,
      position: frame.position,
      fill: frame.fill,
      line: frame.line,
      shadow: frame.shadow,
      ...((frame.geometry === "rect" || frame.geometry === "roundRect")
        ? { borderRadius: frame.radius }
        : {}),
    };
    slide.shapes.add(config);
    counts.native_frames += 1;
  }

  for (const imageModule of model.imageModules) {
    const image = slide.images.add({
      blob: imageModule.bytes,
      contentType: "image/png",
      alt: `[${imageModule.id}] ${imageModule.alt}; portable source: ${imageModule.portable}`,
      fit: imageModule.fit,
      crop: imageModule.crop,
      geometry: imageModule.geometry,
      borderRadius: imageModule.radius,
      position: imageModule.position,
    });
    setStableImageName(image, imageModule.id);
    counts.cropped_png_modules += 1;
  }

  for (const layer of model.networkLayers) {
    for (const partName of ["top", "side", "face"]) {
      const part = layer.parts[partName];
      slide.shapes.add(customPathConfig(part.id, part.points, {
        fill: part.fill,
        line: part.line,
        close: true,
        shadow: part.shadow,
      }));
      counts.native_network_faces += 1;
    }
  }

  for (const plotPath of model.plotPaths) {
    slide.shapes.add(customPathConfig(plotPath.id, plotPath.points, {
      fill: "none",
      line: plotPath.line,
    }));
    counts.native_plot_paths += 1;
  }

  for (const label of model.labels) {
    const shape = slide.shapes.add({
      geometry: "textbox",
      name: label.id,
      position: label.position,
      fill: "none",
      line: { style: "solid", fill: "none", width: 0.1 },
    });
    shape.text = label.text;
    shape.text.style = {
      fontSize: label.fontSize,
      fontFamily: label.fontFamily,
      color: label.color,
      bold: label.bold,
      italic: label.italic,
      alignment: label.alignment,
    };
    counts.native_labels += 1;
  }

  for (const equation of model.equations) {
    const image = slide.images.add({
      blob: equation.bytes,
      contentType: "image/svg+xml",
      alt: `[${equation.id}] ${equation.alt}`,
      fit: "contain",
      position: equation.position,
    });
    setStableImageName(image, equation.id);
    counts.equation_svg_images += 1;
  }

  const notes = [
    "Candidate C high-fidelity hybrid editable figure.",
    `Canonical source: ${model.sourceLabel}`,
    "Raster modules are deliberately bounded, cropped, and replaceable:",
    ...model.imageModules.map((item) => `- ${item.id}: ${item.portable}`),
    "Authoritative equations (embedded SVG with retained LaTeX):",
    ...model.equations.map((item) => `- ${item.equationId}: ${item.latex}`),
    "No full-canvas raster is present; frames, network, plots, labels, connectors, and arrowheads are native objects.",
    "[Sources]",
    ...model.imageModules.map((item) => `- ${item.portable} — local publication-safe figure module.`),
    ...model.equations.map((item) => `- ${item.portable} — locally rendered vector equation.`),
  ];
  notes.forEach((line, index) => assertNoLocalPath(line, `speaker note line ${index + 1}`));
  slide.speakerNotes.textFrame.setText(notes);
  slide.speakerNotes.setVisible(false);

  return { presentation, slide, counts, PresentationFile };
}

async function exportArtifacts(model, specBytes, artifactModule, outputDir) {
  await fs.mkdir(outputDir, { recursive: true });
  const stagingDir = path.join(outputDir, `.hybrid-pptx-staging-${process.pid}-${crypto.randomUUID()}`);
  const committed = [];
  await fs.mkdir(stagingDir);
  try {
    const { presentation, slide, counts, PresentationFile } = await buildPresentation(model, artifactModule);
    const preview = await presentation.export({ slide, format: "png", scale: 1 });
    await writeBlob(path.join(stagingDir, "slide-01.png"), preview);

    const layout = await slide.export({ format: "layout" });
    await fs.writeFile(path.join(stagingDir, "slide-01.layout.json"), await layout.text());

    const inspection = await presentation.inspect({
      kind: "slide,textbox,shape,image,notes",
      maxChars: 100000,
    });
    await fs.writeFile(path.join(stagingDir, "artifact_tool_inspect.ndjson"), inspection.ndjson || "");

    const pptx = await PresentationFile.exportPptx(presentation);
    await pptx.save(path.join(stagingDir, "figure.pptx"));

    const report = {
      schema_version: "1.0",
      status: "AUTHORED_PENDING_VISUAL_QA",
      canonical_source: model.sourceLabel,
      canonical_source_sha256: sha256(specBytes),
      canvas: { width: model.canvas.width, height: model.canvas.height },
      slide_count: 1,
      object_counts: counts,
      raster_modules: model.imageModules.map((item) => ({
        id: item.id,
        role: item.role,
        source: item.portable,
        sha256: sha256(item.bytes),
        crop: item.crop,
      })),
      equation_modules: model.equations.map((item) => ({
        id: item.id,
        equation_id: item.equationId,
        source: item.portable,
        sha256: sha256(item.bytes),
        latex_source: item.latex,
      })),
      constraints: {
        candidate_c_composition: true,
        whole_canvas_raster: false,
        native_frames: true,
        native_network_faces: true,
        native_plot_paths: true,
        native_labels: true,
        native_connectors_and_arrowheads: true,
        equations_are_vector_svg: true,
        equation_latex_retained_in_alt_and_notes: true,
        scientific_approval: false,
      },
      outputs: {
        pptx: "figure.pptx",
        preview: "slide-01.png",
        layout: "slide-01.layout.json",
        inspection: "artifact_tool_inspect.ndjson",
        report: "pptx_artifact_report.json",
      },
      verification_boundary: "Artifact authored; visual inspection, overflow checks, and scientific approval remain separate required steps.",
    };
    const reportText = `${JSON.stringify(report, null, 2)}\n`;
    assertNoLocalPath(reportText, "portable PPTX report");
    await fs.writeFile(path.join(stagingDir, "pptx_artifact_report.json"), reportText);

    for (const name of OUTPUT_NAMES) {
      const source = path.join(stagingDir, name);
      const destination = path.join(outputDir, name);
      await fs.rename(source, destination);
      committed.push(destination);
    }
  } catch (error) {
    for (const filePath of committed.reverse()) {
      await fs.unlink(filePath).catch(() => undefined);
    }
    throw error;
  } finally {
    await fs.rm(stagingDir, { recursive: true, force: true });
  }
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  if (!args) return;
  const paths = {
    spec: path.resolve(args.spec),
    assetDir: path.resolve(args["asset-dir"]),
    equationDir: path.resolve(args["equation-dir"]),
    outputDir: path.resolve(args["output-dir"]),
  };
  await assertInputPath(paths.spec, "--spec", "file");
  if (path.extname(paths.spec).toLowerCase() !== ".json") throw new Error("--spec must be a JSON file");
  await assertInputPath(paths.assetDir, "--asset-dir", "directory");
  await assertInputPath(paths.equationDir, "--equation-dir", "directory");
  await assertOutputsAvailable(paths.outputDir);

  const { value: spec, bytes: specBytes } = await readJson(paths.spec);
  const model = await validateAndLoadSpec(spec, paths);

  const moduleRoot = process.env.RUNTIME_NODE_MODULES;
  if (!moduleRoot || !path.isAbsolute(moduleRoot)) {
    throw new Error("RUNTIME_NODE_MODULES must be set to the bundled absolute module directory");
  }
  const artifactPath = path.join(moduleRoot, "@oai", "artifact-tool", "dist", "artifact_tool.mjs");
  await assertInputPath(artifactPath, "bundled @oai/artifact-tool module", "file");
  const artifactModule = await import(pathToFileURL(artifactPath).href);
  await exportArtifacts(model, specBytes, artifactModule, paths.outputDir);
}

main().catch((error) => {
  process.stderr.write(`${error?.stack || String(error)}\n`);
  process.exitCode = 1;
});
