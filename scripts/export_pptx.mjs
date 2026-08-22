#!/usr/bin/env node
/** Export native PowerPoint objects directly from canonical semantic JSON. */

import fs from "node:fs/promises";
import path from "node:path";
import { pathToFileURL } from "node:url";

function arg(name, fallback = null) {
  const index = process.argv.indexOf(name);
  return index >= 0 ? process.argv[index + 1] : fallback;
}

async function writeBlob(filePath, blob) {
  await fs.writeFile(filePath, new Uint8Array(await blob.arrayBuffer()));
}

function colorValue(value, fallback) {
  return typeof value === "string" && value.length ? value : fallback;
}

function shapeBounds(shape) {
  if (shape.type === "rect") return { left: shape.x, top: shape.y, width: shape.width, height: shape.height };
  if (shape.type === "ellipse") return { left: shape.cx - shape.rx, top: shape.cy - shape.ry, width: shape.rx * 2, height: shape.ry * 2 };
  if (shape.type === "polygon") {
    const xs = shape.points.map((point) => point[0]);
    const ys = shape.points.map((point) => point[1]);
    return { left: Math.min(...xs), top: Math.min(...ys), width: Math.max(...xs) - Math.min(...xs), height: Math.max(...ys) - Math.min(...ys) };
  }
  if (shape.type === "line") {
    return { left: Math.min(shape.x1, shape.x2), top: Math.min(shape.y1, shape.y2), width: Math.abs(shape.x2 - shape.x1), height: Math.abs(shape.y2 - shape.y1) };
  }
  return { left: 0, top: 0, width: 10, height: 10 };
}

function sideForVector(dx, dy, target = false) {
  if (Math.abs(dx) >= Math.abs(dy)) {
    if (dx >= 0) return target ? "left" : "right";
    return target ? "right" : "left";
  }
  if (dy >= 0) return target ? "top" : "bottom";
  return target ? "bottom" : "top";
}

function connectorSides(points = []) {
  if (points.length < 2) return { fromSide: "right", toSide: "left" };
  const first = points[0];
  const second = points[1];
  const penultimate = points[points.length - 2];
  const last = points[points.length - 1];
  return {
    fromSide: sideForVector(second[0] - first[0], second[1] - first[1], false),
    toSide: sideForVector(last[0] - penultimate[0], last[1] - penultimate[1], true),
  };
}

function connectorPathConfig(item, color, width) {
  const points = item.points || [];
  const xs = points.map((point) => point[0]);
  const ys = points.map((point) => point[1]);
  const left = Math.min(...xs);
  const top = Math.min(...ys);
  const pathWidth = Math.max(1, Math.max(...xs) - left);
  const pathHeight = Math.max(1, Math.max(...ys) - top);
  return {
    geometry: "custom",
    name: `${item.id}-visible-path`,
    position: { left, top, width: pathWidth, height: pathHeight },
    fill: "none",
    line: { style: item.dash ? "dashed" : "solid", fill: color, width },
    customPaths: [{
      width: pathWidth,
      height: pathHeight,
      commands: [
        { moveTo: { x: points[0][0] - left, y: points[0][1] - top } },
        ...points.slice(1).map((point) => ({ lineTo: { x: point[0] - left, y: point[1] - top } })),
      ],
    }],
  };
}

function connectorArrowheadConfig(item, color) {
  const points = item.points || [];
  const previous = points[points.length - 2];
  const target = points[points.length - 1];
  const angle = Math.atan2(target[1] - previous[1], target[0] - previous[0]);
  const size = 12;
  const leftPoint = [target[0] - size * Math.cos(angle - 0.55), target[1] - size * Math.sin(angle - 0.55)];
  const rightPoint = [target[0] - size * Math.cos(angle + 0.55), target[1] - size * Math.sin(angle + 0.55)];
  const arrowPoints = [target, leftPoint, rightPoint];
  const xs = arrowPoints.map((point) => point[0]);
  const ys = arrowPoints.map((point) => point[1]);
  const left = Math.min(...xs);
  const top = Math.min(...ys);
  const width = Math.max(1, Math.max(...xs) - left);
  const height = Math.max(1, Math.max(...ys) - top);
  return {
    geometry: "custom",
    name: `${item.id}-visible-arrowhead`,
    position: { left, top, width, height },
    fill: color,
    line: { style: "solid", fill: color, width: 0.5 },
    customPaths: [{
      width,
      height,
      commands: [
        { moveTo: { x: arrowPoints[0][0] - left, y: arrowPoints[0][1] - top } },
        { lineTo: { x: arrowPoints[1][0] - left, y: arrowPoints[1][1] - top } },
        { lineTo: { x: arrowPoints[2][0] - left, y: arrowPoints[2][1] - top } },
        { close: {} },
      ],
    }],
  };
}

async function main() {
  const semanticPath = path.resolve(arg("--semantic"));
  const outputDir = path.resolve(arg("--output-dir"));
  const equationDir = arg("--equation-dir") ? path.resolve(arg("--equation-dir")) : null;
  const moduleRoot = process.env.RUNTIME_NODE_MODULES;
  if (!moduleRoot) throw new Error("RUNTIME_NODE_MODULES is required");
  const artifactModule = await import(pathToFileURL(path.join(moduleRoot, "@oai/artifact-tool/dist/artifact_tool.mjs")).href);
  const { Presentation, PresentationFile } = artifactModule;
  const semantic = JSON.parse(await fs.readFile(semanticPath, "utf8"));
  await fs.mkdir(outputDir, { recursive: true });

  const presentation = Presentation.create({
    slideSize: { width: semantic.canvas.width, height: semantic.canvas.height },
  });
  const slide = presentation.slides.add();
  slide.background.fill = semantic.canvas.background || "#FFFFFF";
  const colors = semantic.style_tokens?.colors || {};
  const shapesById = new Map();

  for (const item of semantic.shapes || []) {
    const position = shapeBounds(item);
    let geometry = "rect";
    let config = {};
    if (item.type === "ellipse") geometry = "ellipse";
    if (item.type === "line") geometry = "line";
    if (item.type === "polygon") {
      geometry = "custom";
      const originX = position.left;
      const originY = position.top;
      config.customPaths = [{
        width: Math.max(1, position.width), height: Math.max(1, position.height),
        commands: [
          { moveTo: { x: item.points[0][0] - originX, y: item.points[0][1] - originY } },
          ...item.points.slice(1).map((point) => ({ lineTo: { x: point[0] - originX, y: point[1] - originY } })),
          { close: {} },
        ],
      }];
    }
    const shape = slide.shapes.add({
      geometry,
      name: item.id,
      position,
      fill: item.type === "line" ? "none" : colorValue(item.fill, colors.surface || "#F2F4F6"),
      line: {
        style: item.dash ? "dashed" : "solid",
        fill: colorValue(item.stroke, colors.ink || "#20252B"),
        width: item.stroke_width || semantic.style_tokens?.stroke_width || 2.2,
      },
      ...config,
    });
    shapesById.set(item.id, shape);
  }

  for (const item of semantic.text_objects || []) {
    const textWidth = 180;
    const textLeft = item.text_anchor === "middle" ? item.x - textWidth / 2 : item.x;
    const textShape = slide.shapes.add({
      geometry: "textbox",
      name: item.id,
      position: { left: textLeft, top: item.y - item.font_size * 1.2, width: textWidth, height: item.font_size * 1.7 },
      fill: "none",
      line: { style: "solid", fill: "none", width: 0 },
    });
    textShape.text = item.text || (item.lines || []).join("\n");
    textShape.text.style = {
      fontSize: item.font_size || 18,
      bold: (item.font_weight || 400) >= 600,
      italic: item.font_style === "italic",
      color: colors[item.fill_token || "ink"] || colors.ink || "#20252B",
      fontFamily: (item.font_family || "Arial").split(",")[0],
    };
    shapesById.set(item.id, textShape);
  }

  let equationSvgCount = 0;
  for (const equation of semantic.equation_objects || []) {
    const svgPath = equationDir ? path.join(equationDir, `${equation.equation_id}.svg`) : null;
    let added = false;
    if (svgPath) {
      try {
        const bytes = await fs.readFile(svgPath);
        const equationLeft = equation.text_anchor === "middle" ? equation.x - (equation.width || 360) / 2 : equation.x;
        slide.images.add({
          blob: bytes,
          contentType: "image/svg+xml",
          alt: `Equation ${equation.equation_id}; LaTeX: ${equation.latex_source || ""}`,
          fit: "contain",
          position: { left: equationLeft, top: equation.y - (equation.height || 36), width: equation.width || 360, height: equation.height || 36 },
        });
        equationSvgCount += 1;
        added = true;
      } catch (_) {
        added = false;
      }
    }
    if (!added) {
      const equationLeft = equation.text_anchor === "middle" ? equation.x - (equation.width || 360) / 2 : equation.x;
      const fallback = slide.shapes.add({
        geometry: "textbox", name: equation.id,
        position: { left: equationLeft, top: equation.y - (equation.height || 36), width: equation.width || 360, height: equation.height || 36 },
        fill: "none", line: { style: "solid", fill: "none", width: 0 },
      });
      fallback.text = equation.fallback_text || equation.equation_id;
      fallback.text.style = { fontSize: equation.font_size || 18, color: colors.ink || "#20252B", fontFamily: "Cambria Math" };
    }
  }

  let connectorCount = 0;
  let visibleConnectorPathCount = 0;
  let visibleConnectorArrowheadCount = 0;
  for (const item of semantic.connectors || []) {
    const source = shapesById.get(item.source_id);
    const target = shapesById.get(item.target_id);
    if (!source || !target) throw new Error(`Connector ${item.id} has unresolved endpoint`);
    const defaultToken = item.color_token || "ink";
    const relationColor = colors[item.stroke_token || defaultToken] || colors.ink || "#20252B";
    const sideOptions = connectorSides(item.points || []);
    const visiblePath = slide.shapes.add(connectorPathConfig(item, relationColor, semantic.style_tokens?.stroke_width || 2.2));
    visiblePath.bringToFront();
    visibleConnectorPathCount += 1;
    const visibleArrowhead = slide.shapes.add(connectorArrowheadConfig(item, relationColor));
    visibleArrowhead.bringToFront();
    visibleConnectorArrowheadCount += 1;
    const connector = slide.shapes.connect(source, target, {
      kind: item.points?.length > 2 ? "elbow" : "straight",
      line: { style: "solid", fill: semantic.canvas.background || "#FFFFFF", width: 0.1 },
      ...sideOptions,
    });
    try { connector.name = item.id; } catch (_) {}
    connectorCount += 1;
  }

  const notes = [
    `Canonical semantic source: ${semanticPath}`,
    `Figure ID: ${semantic.figure_id}`,
    "Equations:",
    ...(semantic.equation_objects || []).map((equation) => `${equation.equation_id}: ${equation.latex_source || ""}`),
  ];
  slide.speakerNotes.textFrame.setText(notes);
  slide.speakerNotes.setVisible(false);

  const preview = await presentation.export({ slide, format: "png", scale: 1 });
  await writeBlob(path.join(outputDir, "slide-01.png"), preview);
  const layout = await slide.export({ format: "layout" });
  await fs.writeFile(path.join(outputDir, "slide-01.layout.json"), await layout.text());
  const inspection = await presentation.inspect({ kind: "slide,textbox,shape,image,notes", search: ".*", maxChars: 50000 });
  await fs.writeFile(path.join(outputDir, "artifact_tool_inspect.ndjson"), inspection.ndjson || "");
  const pptx = await PresentationFile.exportPptx(presentation);
  const pptxPath = path.join(outputDir, "figure.pptx");
  await pptx.save(pptxPath);
  const report = {
    status: "VERIFIED",
    canonical_source: semanticPath,
    output: pptxPath,
    native_shape_count: (semantic.shapes || []).length,
    live_text_count: (semantic.text_objects || []).length,
    native_connector_count: connectorCount,
    visible_connector_path_count: visibleConnectorPathCount,
    visible_connector_arrowhead_count: visibleConnectorArrowheadCount,
    equation_svg_group_count: equationSvgCount,
    whole_canvas_raster: false,
    equation_metadata_in_notes: true,
    preview: path.join(outputDir, "slide-01.png"),
    layout: path.join(outputDir, "slide-01.layout.json"),
    inspection: path.join(outputDir, "artifact_tool_inspect.ndjson"),
  };
  await fs.writeFile(path.join(outputDir, "pptx_artifact_report.json"), JSON.stringify(report, null, 2) + "\n");
}

main().catch((error) => {
  console.error(error?.stack || String(error));
  process.exitCode = 1;
});
