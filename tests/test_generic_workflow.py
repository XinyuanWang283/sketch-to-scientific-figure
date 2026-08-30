#!/usr/bin/env python3
"""Public regression tests for the generic sketch-to-figure workflow."""

from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from types import SimpleNamespace


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = REPOSITORY_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from build_figure_editorial_review import OVERLAY_END, OVERLAY_START  # noqa: E402
from build_fixture_semantic_source import build as build_semantic_source  # noqa: E402
from compile_figure_artifacts import compile_run  # noqa: E402
from figure_artifacts import load_json, sha256_file, word_count, write_json  # noqa: E402
from render_topology_skeleton import render as render_skeleton  # noqa: E402
from run_workflow import run  # noqa: E402
from validate_figure_artifacts import validate as validate_artifacts  # noqa: E402
from validate_semantic_svg import validate_svg  # noqa: E402
from workflow_v3 import render_semantic_svg, validate_schema  # noqa: E402


def args_for(mode: str, run_dir: Path, **overrides: object) -> SimpleNamespace:
    values = {
        "mode": mode,
        "run_dir": run_dir,
        "resume": False,
        "decision": None,
        "truth": None,
        "paper_source": [],
        "sketch": None,
        "visual_plan": None,
        "approved_wireframe": None,
        "approved_wireframe_png": None,
        "fixture_svg": None,
        "fixture_spec": None,
        "register_png": None,
        "register_delivery": None,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def write_generic_contract_fixture(run_dir: Path) -> tuple[Path, Path]:
    """Create minimal test-only truth and blueprint data outside the repository."""

    source_path = run_dir / "sources" / "method.txt"
    source_path.parent.mkdir(parents=True, exist_ok=True)
    source_path.write_text(
        "One abstract input passes through one transform to produce one output.\n",
        encoding="utf-8",
    )
    truth_path = run_dir / "truth" / "scientific_truth.json"
    write_json(
        truth_path,
        {
            "schema_version": "1.0",
            "figure_id": "generic_contract_fixture",
            "message": {
                "one_sentence": "One abstract input passes through one transform to produce one output.",
                "visual_message": "Show one generic left-to-right input, transform, and output path.",
                "audience": "scientific software developers",
            },
            "provenance": {
                "sources": [
                    {
                        "path": "sources/method.txt",
                        "sha256": sha256_file(source_path),
                        "role": "test-only method statement",
                    }
                ]
            },
            "stages": [
                {"id": "input", "label": "Input"},
                {"id": "process", "label": "Process"},
                {"id": "output", "label": "Output"},
            ],
            "entities": [
                {"id": "input", "type": "input", "label": "Input"},
                {"id": "transform", "type": "operator", "label": "Transform"},
                {"id": "output", "type": "output", "label": "Output"},
            ],
            "instances": [
                {
                    "id": "input_x",
                    "entity_ref": "input",
                    "type": "input",
                    "stage": "input",
                    "label": "x",
                    "shape": "circle",
                    "visual_role": "input",
                },
                {
                    "id": "transform_instance",
                    "entity_ref": "transform",
                    "type": "operator",
                    "stage": "process",
                    "label": "T",
                    "shape": "operator",
                    "visual_role": "process",
                },
                {
                    "id": "output_z",
                    "entity_ref": "output",
                    "type": "output",
                    "stage": "output",
                    "label": "z",
                    "shape": "square",
                    "visual_role": "output",
                },
            ],
            "relations": [
                {
                    "id": "input_feeds_transform",
                    "type": "feeds",
                    "source": "input_x",
                    "target": "transform_instance",
                    "rule_ids": ["ARTIFACT_REFERENCE_INTEGRITY"],
                },
                {
                    "id": "transform_produces_output",
                    "type": "produces",
                    "source": "transform_instance",
                    "target": "output_z",
                    "rule_ids": ["ARTIFACT_REFERENCE_INTEGRITY"],
                },
            ],
            "equations": [
                {
                    "id": "generic_mapping",
                    "latex": "z=T(x)",
                    "role": "generic mapping",
                }
            ],
            "invariants": [
                {"rule_id": "ARTIFACT_SOURCE_HASHES"},
                {"rule_id": "ARTIFACT_REFERENCE_INTEGRITY"},
                {"rule_id": "BLUEPRINT_TRUTH_COVERAGE"},
            ],
            "forbidden_implications": [
                {
                    "id": "no_performance_claim",
                    "description": "Do not imply measured performance.",
                }
            ],
            "sketch_locks": [],
            "flexibility_zones": [
                {"id": "style", "allowed": ["palette", "spacing"]}
            ],
            "unresolved_ambiguities": [],
            "information_profiles": {
                "main_paper_story_first": {
                    "exact_text": ["Input", "Transform", "Output"],
                    "displayed_equation_ids": ["generic_mapping"],
                    "minimum_font_size_pt": 8.0,
                }
            },
        },
    )
    blueprint_path = run_dir / "blueprints" / "generic_contract_fixture.json"
    write_json(
        blueprint_path,
        {
            "schema_version": "1.0",
            "candidate_id": "generic_contract_fixture",
            "truth_ref": {
                "path": "truth/scientific_truth.json",
                "sha256": sha256_file(truth_path),
            },
            "layout_fingerprint": {
                "reading_axis": "left-to-right",
                "region_graph": ["input", "process", "output"],
                "dominant_region": "process",
                "stage_arrangement": "three aligned regions",
                "repetition_strategy": "none",
                "audit_location": "caption",
                "symmetry": "balanced around the transform",
                "connector_topology": "single directed path",
                "occupied_area_distribution": [0.2, 0.4, 0.2],
            },
            "regions": [
                {"id": "input", "label": "Input", "bbox": [0.04, 0.2, 0.22, 0.6]},
                {"id": "process", "label": "Process", "bbox": [0.34, 0.14, 0.32, 0.72]},
                {"id": "output", "label": "Output", "bbox": [0.74, 0.2, 0.22, 0.6]},
            ],
            "nodes": [
                {
                    "id": "input_node",
                    "type": "input",
                    "bbox": [0.10, 0.36, 0.10, 0.24],
                    "instance_refs": ["input_x"],
                    "layout": "horizontal",
                },
                {
                    "id": "transform_node",
                    "type": "operator",
                    "bbox": [0.4, 0.35, 0.2, 0.3],
                    "instance_refs": ["transform_instance"],
                    "layout": "horizontal",
                },
                {
                    "id": "output_node",
                    "type": "output",
                    "bbox": [0.80, 0.36, 0.10, 0.24],
                    "instance_refs": ["output_z"],
                    "layout": "horizontal",
                },
            ],
            "ports": [
                {"id": "input_node.out", "node_id": "input_node", "name": "out", "position": "right"},
                {"id": "transform_node.in", "node_id": "transform_node", "name": "in", "position": "left"},
                {"id": "transform_node.out", "node_id": "transform_node", "name": "out", "position": "right"},
                {"id": "output_node.in", "node_id": "output_node", "name": "in", "position": "left"},
            ],
            "edges": [
                {
                    "id": "edge_input_transform",
                    "source": "input_node.out",
                    "target": "transform_node.in",
                    "relation_types": ["feeds"],
                    "routing": "horizontal",
                    "arrow": True,
                },
                {
                    "id": "edge_transform_output",
                    "source": "transform_node.out",
                    "target": "output_node.in",
                    "relation_types": ["produces"],
                    "routing": "horizontal",
                    "arrow": True,
                },
            ],
            "required_visual_relations": [
                "input_feeds_transform",
                "transform_produces_output",
            ],
            "in_scope_rule_ids": [
                "ARTIFACT_REQUIRED_FIELDS",
                "ARTIFACT_SCHEMA_VALIDITY",
                "ARTIFACT_SOURCE_HASHES",
                "ARTIFACT_UNIQUE_IDS",
                "ARTIFACT_REFERENCE_INTEGRITY",
                "BLUEPRINT_TRUTH_COVERAGE",
                "BLUEPRINT_FINGERPRINT_DIVERSITY",
            ],
            "allowed_flexibility": ["palette", "spacing"],
            "deliberate_omissions": ["measurements", "results"],
            "complexity_budget": {
                "hero_groups": 3,
                "displayed_equations": 1,
                "ordinary_prose_labels": 3,
                "connector_count": 2,
            },
            "visible_text_whitelist": ["Input", "Transform", "Output"],
            "connector_style": "orthogonal",
            "art_direction": {
                "composition": "one calm left-to-right scientific path",
                "shape_language": "simple native vector glyphs",
                "color": "restrained and grayscale-safe",
                "whitespace": "generous outer margins",
                "connectors": "quiet orthogonal arrows",
            },
        },
    )
    return truth_path, blueprint_path


class GenericWorkflowTests(unittest.TestCase):
    def test_generic_contract_compiles_renders_and_validates(self) -> None:
        with tempfile.TemporaryDirectory(prefix="generic-contract-") as temporary:
            run_dir = Path(temporary) / "run"
            truth_path, blueprint_path = write_generic_contract_fixture(run_dir)
            summary = compile_run(run_dir, REPOSITORY_ROOT)
            self.assertEqual(summary["candidate_count"], 1)
            self.assertEqual(
                summary["compiled"][0]["candidate_id"],
                "generic_contract_fixture",
            )

            compiled_artifacts = [
                "rules/validation_rules.json",
                "skeletons/fingerprint_report.json",
                "generation/generic_contract_fixture_prompt.md",
                "generation/generation_manifest.json",
                "reviews/generic_contract_fixture_review.template.json",
                "selected/generic_contract_fixture_selected_candidate_map.template.json",
                "svg/generic_contract_fixture_reconstruction_spec.json",
                "validation/compile_report.json",
            ]
            for relative in compiled_artifacts:
                with self.subTest(compiled_artifact=relative):
                    path = run_dir / relative
                    self.assertTrue(path.is_file(), relative)
                    self.assertGreater(path.stat().st_size, 0, relative)

            fingerprint = load_json(run_dir / "skeletons" / "fingerprint_report.json")
            self.assertEqual(len(fingerprint["candidates"]), 1)
            self.assertEqual(fingerprint["pairs"], [])

            compile_report = load_json(run_dir / "validation" / "compile_report.json")
            self.assertEqual(compile_report, summary)
            truth_hash = sha256_file(truth_path)
            blueprint_hash = sha256_file(blueprint_path)
            prompt_path = run_dir / "generation" / "generic_contract_fixture_prompt.md"
            prompt_hash = sha256_file(prompt_path)
            prompt_words = word_count(prompt_path.read_text(encoding="utf-8"))
            self.assertEqual(summary["truth_sha256"], truth_hash)
            self.assertEqual(summary["compiled"][0]["blueprint_sha256"], blueprint_hash)
            self.assertEqual(summary["compiled"][0]["prompt_sha256"], prompt_hash)
            self.assertEqual(summary["compiled"][0]["prompt_word_count"], prompt_words)

            generation_manifest = load_json(
                run_dir / "generation" / "generation_manifest.json"
            )
            self.assertEqual(len(generation_manifest["entries"]), 1)
            manifest_entry = generation_manifest["entries"][0]
            self.assertEqual(manifest_entry["candidate_id"], "generic_contract_fixture")
            self.assertEqual(
                manifest_entry["prompt_path"],
                "generation/generic_contract_fixture_prompt.md",
            )
            self.assertEqual(manifest_entry["prompt_sha256"], prompt_hash)
            self.assertEqual(manifest_entry["prompt_word_count"], prompt_words)
            self.assertFalse(manifest_entry["generation_call_completed"])
            self.assertIsNone(manifest_entry["output_path"])

            review = load_json(
                run_dir / "reviews" / "generic_contract_fixture_review.template.json"
            )
            self.assertEqual(review["candidate_id"], "generic_contract_fixture")
            self.assertEqual(review["truth_hash"], truth_hash)
            self.assertEqual(review["blueprint_hash"], blueprint_hash)
            self.assertEqual(review["prompt_hash"], prompt_hash)

            reconstruction_spec = load_json(
                run_dir / "svg" / "generic_contract_fixture_reconstruction_spec.json"
            )
            self.assertEqual(
                reconstruction_spec["truth_ref"],
                {
                    "path": "truth/scientific_truth.json",
                    "sha256": truth_hash,
                },
            )
            self.assertEqual(
                reconstruction_spec["blueprint_ref"],
                {
                    "path": "blueprints/generic_contract_fixture.json",
                    "sha256": blueprint_hash,
                },
            )
            self.assertEqual(reconstruction_spec["exact_equations"], ["z=T(x)"])

            rendered = render_skeleton(
                truth_path,
                blueprint_path,
                run_dir / "skeletons",
            )
            self.assertEqual(set(rendered), {"scene", "svg", "png"})
            for kind, value in rendered.items():
                with self.subTest(rendered_artifact=kind):
                    path = Path(value)
                    self.assertTrue(path.is_file(), value)
                    self.assertGreater(path.stat().st_size, 0, value)

            scene = load_json(Path(rendered["scene"]))
            self.assertEqual(
                {item["id"] for item in scene["objects"]},
                {"input_x", "transform_instance", "output_z"},
            )
            connectors = {item["id"]: item for item in scene["connectors"]}
            self.assertEqual(
                {
                    connector_id: (item["source"], item["target"])
                    for connector_id, item in connectors.items()
                },
                {
                    "input_feeds_transform": ("input_x", "transform_instance"),
                    "transform_produces_output": ("transform_instance", "output_z"),
                },
            )
            for connector in connectors.values():
                self.assertTrue(connector["arrow"])
                self.assertGreaterEqual(len(connector["points"]), 2)
                for start, end in zip(connector["points"], connector["points"][1:]):
                    self.assertTrue(
                        abs(start[0] - end[0]) <= 1e-6
                        or abs(start[1] - end[1]) <= 1e-6
                    )

            ET.parse(rendered["svg"])
            from PIL import Image

            with Image.open(rendered["png"]) as image:
                self.assertEqual(image.size, (1600, 900))
                image.verify()

            report = validate_artifacts(run_dir, REPOSITORY_ROOT, run_dir)
            self.assertEqual(report["summary"]["overall"], "pass")
            self.assertEqual(report["summary"]["failed"], 0)
            self.assertEqual(report["summary"]["blockers"], 0)
            self.assertEqual(report["scene_count"], 1)
            report_path = run_dir / "validation" / "artifact_report.json"
            self.assertTrue(report_path.is_file())
            self.assertEqual(load_json(report_path), report)

    def test_repository_schemas_and_rules_parse(self) -> None:
        paths = sorted((REPOSITORY_ROOT / "schemas").glob("*.json"))
        paths += sorted((REPOSITORY_ROOT / "rules").glob("*.json"))
        self.assertGreaterEqual(len(paths), 10)
        for path in paths:
            with self.subTest(path=path.name):
                self.assertIsInstance(load_json(path), dict)

    def test_generic_semantic_svg_passes_and_detects_broken_connector(self) -> None:
        fixture_dir = REPOSITORY_ROOT / "tests" / "fixtures"
        source_svg = fixture_dir / "generic_semantic_pass.svg"
        spec = fixture_dir / "generic_svg_fixture_spec.json"
        report = validate_svg(source_svg, spec)
        self.assertEqual(report["summary"]["overall"], "pass")

        with tempfile.TemporaryDirectory(prefix="generic-svg-failure-") as temporary:
            tree = ET.parse(source_svg)
            connector = next(
                element
                for element in tree.getroot().iter()
                if element.get("id") == "flow-input-model"
            )
            connector.attrib.pop("data-target")
            mutated = Path(temporary) / "broken.svg"
            tree.write(mutated, encoding="utf-8", xml_declaration=True)
            failed = validate_svg(mutated, spec)
            failures = {
                check["rule_id"]
                for check in failed["checks"]
                if check["status"] == "fail"
            }
            self.assertIn("SVG_SOURCE_TARGET_METADATA", failures)

    def test_semantic_builder_supports_generic_groups_connectors_and_equations(self) -> None:
        fixture_dir = REPOSITORY_ROOT / "tests" / "fixtures"
        with tempfile.TemporaryDirectory(prefix="generic-semantic-builder-") as temporary:
            run_dir = Path(temporary) / "run"
            report = build_semantic_source(
                fixture_dir / "generic_semantic_pass.svg",
                fixture_dir / "generic_svg_fixture_spec.json",
                run_dir,
                figure_id="generic-builder-test",
            )
            self.assertEqual(report["connector_count"], 2)
            semantic = load_json(run_dir / "source" / "semantic_figure.json")
            self.assertEqual(semantic["figure_id"], "generic-builder-test")
            self.assertEqual(len(semantic["equation_objects"]), 2)
            self.assertEqual(semantic["canvas"]["physical_width_mm"], 180.0)
            self.assertEqual(semantic["style_tokens"]["colors"]["muted"], "#64748B")
            rendered = render_semantic_svg(semantic, profile="svg")
            self.assertIn('width="180.0mm"', rendered)
            self.assertIn('data-latex="f_\\theta"', rendered)
            rendered_path = run_dir / "rendered.svg"
            rendered_path.write_text(rendered, encoding="utf-8")
            self.assertEqual(
                validate_svg(rendered_path, fixture_dir / "generic_svg_fixture_spec.json")["summary"]["overall"],
                "pass",
            )

    def test_fixture_runs_all_adapters_without_image_generation(self) -> None:
        if not os.environ.get("RUNTIME_NODE_MODULES"):
            self.skipTest("bundled artifact-tool runtime not configured")
        with tempfile.TemporaryDirectory(prefix="generic-adapter-fixture-") as temporary:
            run_dir = Path(temporary) / "run"
            state = run(args_for("fixture", run_dir))
            self.assertEqual(state["state"], "FIXTURE_COMPLETE")
            self.assertEqual(state["provenance"]["image_generation_calls"], 0)
            expected = [
                "source/semantic_figure.json",
                "source/equations.tex",
                "master/master.svg",
                "delivery/svg/master.svg",
                "delivery/figma/figure_figma.svg",
                "delivery/pptx/figure.pptx",
                "delivery/drawio/figure.drawio",
                "delivery/pdf/publication.pdf",
                "delivery/pdf/grayscale.pdf",
                "delivery/delivery_manifest.json",
                "validation/cross_format_report.json",
                "validation/cross_format_preview.png",
            ]
            for relative in expected:
                self.assertTrue((run_dir / relative).exists(), relative)
            report = load_json(run_dir / "validation" / "cross_format_report.json")
            self.assertEqual(report["status"], "VERIFIED")

    def test_generic_sketch_mode_stops_at_gate_1(self) -> None:
        from PIL import Image, ImageDraw

        fixture_dir = REPOSITORY_ROOT / "tests" / "fixtures"
        with tempfile.TemporaryDirectory(prefix="generic-sketch-mode-") as temporary:
            temporary_dir = Path(temporary)
            run_dir = temporary_dir / "run"
            truth = temporary_dir / "scientific_truth.json"
            truth.write_text(json.dumps({
                "figure_id": "synthetic_restoration_test",
                "message": {
                    "one_sentence": "A synthetic measurement passes through one model to produce an editable estimate.",
                    "visual_message": "Show a clear left-to-right measurement, model, and estimate path.",
                    "audience": "scientific software researchers"
                },
                "provenance": {"sources": []},
                "entities": [],
                "instances": [],
                "relations": [],
                "equations": [],
                "invariants": [],
                "forbidden_implications": [{"id": "performance", "description": "Do not imply measured performance."}],
                "sketch_locks": [],
                "flexibility_zones": [],
                "unresolved_ambiguities": []
            }), encoding="utf-8")
            method = temporary_dir / "method.md"
            method.write_text("A synthetic measurement enters one abstract restoration model and produces one estimate.\n", encoding="utf-8")
            contract = temporary_dir / "contract.md"
            contract.write_text("Keep the left-to-right relation and do not add performance claims.\n", encoding="utf-8")
            sketch = temporary_dir / "sketch.png"
            sketch_image = Image.new("RGB", (1200, 675), "white")
            draw = ImageDraw.Draw(sketch_image)
            draw.ellipse((120, 250, 300, 430), outline="black", width=4)
            draw.rectangle((470, 235, 730, 445), outline="black", width=4)
            draw.rectangle((930, 260, 1080, 420), outline="black", width=4)
            draw.line((300, 340, 470, 340), fill="black", width=4)
            draw.line((730, 340, 930, 340), fill="black", width=4)
            sketch_image.save(sketch)

            approved_wireframe = temporary_dir / "approved_wireframe.svg"
            shutil.copyfile(fixture_dir / "generic_semantic_pass.svg", approved_wireframe)
            approved_preview = temporary_dir / "approved_wireframe.png"
            preview = Image.new("RGB", (1200, 675), "#FCFCFD")
            preview_draw = ImageDraw.Draw(preview)
            preview_draw.text((470, 325), "Approved synthetic wireframe", fill="#1F2937")
            preview.save(approved_preview)
            visual_plan = temporary_dir / "visual_plan.json"
            visual_plan.write_text(json.dumps({
                "schema_version": "1.0",
                "case_id": "synthetic_restoration_test",
                "visual_mode": "guided_redesign",
                "status": "approved",
                "spatial_locks": ["left-to-right measurement-model-estimate order"],
                "allowed_changes": ["spacing", "style", "one removable message cue"],
                "forbidden_visual_grammars": ["dashboard cards", "data-like clinical imagery"],
                "text_policy": {"short_labels_only": True, "footer": False},
                "wireframe_artifacts": {
                    "wireframe_svg": approved_wireframe.name,
                    "wireframe_png": approved_preview.name
                },
                "approval_gate": {
                    "image_generation_authorized": True,
                    "approved_wireframe_revision": 1,
                    "approved_wireframe_sha256": sha256_file(approved_preview)
                }
            }), encoding="utf-8")

            state = run(args_for(
                "sketch",
                run_dir,
                truth=truth,
                paper_source=[method, contract],
                sketch=sketch,
                visual_plan=visual_plan,
                approved_wireframe=approved_wireframe,
                approved_wireframe_png=approved_preview,
            ))
            self.assertEqual(state["state"], "GATE_1_EDITORIAL_STORY_WIREFRAME")
            self.assertEqual(state["gate_status"]["gate_1"], "awaiting_human")
            self.assertEqual(state["provenance"]["image_generation_calls"], 0)
            review = load_json(run_dir / "editorial" / "figure_editorial_review.json")
            self.assertEqual(validate_schema(review, "figure_editorial_review.schema.json"), [])
            classifications = {item["classification"] for item in review["items"]}
            self.assertTrue({"keep", "must-add", "simplify", "remove", "move-to-caption"}.issubset(classifications))

            conservative = run_dir / "editorial" / "wireframe_conservative.svg"
            recommended = run_dir / "editorial" / "wireframe_recommended.svg"
            self.assertEqual(sha256_file(conservative), sha256_file(approved_wireframe))
            base_text = conservative.read_text(encoding="utf-8")
            recommended_text = recommended.read_text(encoding="utf-8")
            self.assertIn('id="paper-aware-overlay"', recommended_text)
            overlay_start = recommended_text.index(OVERLAY_START)
            overlay_end = recommended_text.index(OVERLAY_END) + len(OVERLAY_END)
            self.assertEqual(recommended_text[:overlay_start] + recommended_text[overlay_end:], base_text)

    def test_sketch_mode_requires_visual_plan_binding(self) -> None:
        with tempfile.TemporaryDirectory(prefix="generic-missing-plan-") as temporary:
            placeholder = Path(temporary) / "placeholder.txt"
            placeholder.write_text("placeholder", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "--visual-plan"):
                run(args_for(
                    "sketch",
                    Path(temporary) / "run",
                    truth=placeholder,
                    paper_source=[placeholder],
                    sketch=placeholder,
                ))


if __name__ == "__main__":
    unittest.main()
