#!/usr/bin/env python3
"""Shared helpers for the scientific-figure artifact toolchain.

The module intentionally uses only the Python standard library.  JSON Schema
files document the public artifact contract; these helpers implement the small
set of structural checks needed by the repository's P0 workflow.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Sequence, Set, Tuple


ARTIFACT_REQUIRED_FIELDS: Dict[str, Sequence[str]] = {
    "scientific_truth": (
        "schema_version",
        "figure_id",
        "message",
        "provenance",
        "entities",
        "instances",
        "relations",
        "equations",
        "invariants",
        "forbidden_implications",
        "sketch_locks",
        "flexibility_zones",
        "unresolved_ambiguities",
    ),
    "candidate_blueprint": (
        "schema_version",
        "candidate_id",
        "truth_ref",
        "layout_fingerprint",
        "regions",
        "nodes",
        "ports",
        "edges",
        "required_visual_relations",
        "in_scope_rule_ids",
        "allowed_flexibility",
        "deliberate_omissions",
        "complexity_budget",
    ),
    "review_result": (
        "candidate_id",
        "truth_hash",
        "blueprint_hash",
        "prompt_hash",
        "image_hash",
        "machine_checks",
        "human_checks",
        "blocking_failures",
        "acceptable_raster_imperfections",
        "svg_reconstruction_fixes",
        "repair_budget_used",
        "decision",
        "decision_reason",
    ),
    "selected_candidate_map": (
        "candidate_id",
        "image_hash",
        "major_region_bboxes",
        "palette_samples",
        "stroke_character",
        "corner_language",
        "whitespace_rhythm",
        "glyph_reference_crops",
        "art_direction_notes",
        "scientific_overrides",
    ),
    "svg_reconstruction_spec": (
        "truth_ref",
        "blueprint_ref",
        "selected_candidate_map_ref",
        "native_object_inventory",
        "semantic_group_inventory",
        "exact_text",
        "exact_equations",
        "ports",
        "connectors",
        "geometry_policy",
        "style_tokens",
        "raster_asset_policy",
        "editability_requirements",
        "validation_rule_ids",
    ),
    "validation_rules": ("schema_version", "rules"),
}

FINGERPRINT_FIELDS: Tuple[str, ...] = (
    "reading_axis",
    "region_graph",
    "dominant_region",
    "stage_arrangement",
    "repetition_strategy",
    "audit_location",
    "symmetry",
    "connector_topology",
)


class ArtifactError(ValueError):
    """Raised when an artifact violates the repository contract."""


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def json_schema_errors(instance: Any, schema: Mapping[str, Any]) -> List[str]:
    """Validate the JSON Schema subset used by this repository.

    Supported keywords are local ``$ref``, ``allOf``, ``anyOf``, ``if``/``then``/``else``,
    ``type``, ``required``, ``properties``, ``items``, ``enum``, ``const``, ``pattern``,
    ``minItems``, ``maxItems``, ``uniqueItems``, ``minimum``, and ``maximum``.
    The public schemas deliberately stay inside this subset so P0 needs no
    third-party dependency.
    """

    errors: List[str] = []

    def resolve_ref(reference: str) -> Mapping[str, Any]:
        if not reference.startswith("#/"):
            raise ArtifactError("unsupported non-local schema ref %s" % reference)
        value: Any = schema
        for token in reference[2:].split("/"):
            token = token.replace("~1", "/").replace("~0", "~")
            value = value[token]
        if not isinstance(value, Mapping):
            raise ArtifactError("schema ref %s does not resolve to an object" % reference)
        return value

    def type_matches(value: Any, expected: str) -> bool:
        if expected == "object":
            return isinstance(value, Mapping)
        if expected == "array":
            return isinstance(value, list)
        if expected == "string":
            return isinstance(value, str)
        if expected == "number":
            return isinstance(value, (int, float)) and not isinstance(value, bool)
        if expected == "integer":
            return isinstance(value, int) and not isinstance(value, bool)
        if expected == "boolean":
            return isinstance(value, bool)
        if expected == "null":
            return value is None
        return False

    def visit(value: Any, rule: Mapping[str, Any], path: str) -> None:
        if "$ref" in rule:
            try:
                visit(value, resolve_ref(str(rule["$ref"])), path)
            except (ArtifactError, KeyError) as exc:
                errors.append("%s: %s" % (path, exc))
            return
        for part in rule.get("allOf", []):
            visit(value, part, path)

        def matches(candidate_rule: Mapping[str, Any]) -> bool:
            start = len(errors)
            visit(value, candidate_rule, path)
            matched = len(errors) == start
            del errors[start:]
            return matched

        if "if" in rule and isinstance(rule["if"], Mapping):
            branch = rule.get("then") if matches(rule["if"]) else rule.get("else")
            if isinstance(branch, Mapping):
                visit(value, branch, path)
        if "anyOf" in rule:
            alternatives = [item for item in rule["anyOf"] if isinstance(item, Mapping)]
            if alternatives and not any(matches(item) for item in alternatives):
                errors.append("%s: value does not satisfy anyOf" % path)

        expected_type = rule.get("type")
        if expected_type is not None:
            allowed_types = [expected_type] if isinstance(expected_type, str) else list(expected_type)
            if not any(type_matches(value, item) for item in allowed_types):
                errors.append("%s: expected type %s" % (path, allowed_types))
                return

        if "enum" in rule and value not in rule["enum"]:
            errors.append("%s: value %r not in enum" % (path, value))
        if "const" in rule and value != rule["const"]:
            errors.append("%s: value %r does not equal const %r" % (path, value, rule["const"]))

        if isinstance(value, Mapping):
            for key in rule.get("required", []):
                if key not in value:
                    errors.append("%s: missing required property %s" % (path, key))
            properties = rule.get("properties", {})
            for key, child_rule in properties.items():
                if key in value:
                    visit(value[key], child_rule, "%s.%s" % (path, key))

        if isinstance(value, list):
            if len(value) < int(rule.get("minItems", 0)):
                errors.append("%s: has %d items below minItems" % (path, len(value)))
            if "maxItems" in rule and len(value) > int(rule["maxItems"]):
                errors.append("%s: has %d items above maxItems" % (path, len(value)))
            if rule.get("uniqueItems"):
                encoded = [json.dumps(item, sort_keys=True, ensure_ascii=False) for item in value]
                if len(encoded) != len(set(encoded)):
                    errors.append("%s: items are not unique" % path)
            item_rule = rule.get("items")
            if isinstance(item_rule, Mapping):
                for index, child in enumerate(value):
                    visit(child, item_rule, "%s[%d]" % (path, index))

        if isinstance(value, str) and "pattern" in rule and re.search(str(rule["pattern"]), value) is None:
            errors.append("%s: value %r does not match %s" % (path, value, rule["pattern"]))
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            if "minimum" in rule and value < rule["minimum"]:
                errors.append("%s: value %s below minimum %s" % (path, value, rule["minimum"]))
            if "maximum" in rule and value > rule["maximum"]:
                errors.append("%s: value %s above maximum %s" % (path, value, rule["maximum"]))

    visit(instance, schema, "$")
    return errors


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, ensure_ascii=False, sort_keys=False)
        handle.write("\n")


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_json_sha256(data: Any) -> str:
    encoded = json.dumps(
        data, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return sha256_bytes(encoded)


def word_count(text: str) -> int:
    return len(re.findall(r"\b[\w'’-]+\b", text, flags=re.UNICODE))


def require_fields(data: Mapping[str, Any], artifact_type: str) -> List[str]:
    required = ARTIFACT_REQUIRED_FIELDS.get(artifact_type)
    if required is None:
        return ["unknown artifact type: %s" % artifact_type]
    return ["missing required field: %s" % key for key in required if key not in data]


def duplicate_values(values: Iterable[str]) -> List[str]:
    seen: Set[str] = set()
    duplicates: Set[str] = set()
    for value in values:
        if value in seen:
            duplicates.add(value)
        seen.add(value)
    return sorted(duplicates)


def truth_instance_index(truth: Mapping[str, Any]) -> Dict[str, Mapping[str, Any]]:
    return {item["id"]: item for item in truth.get("instances", [])}


def truth_entity_index(truth: Mapping[str, Any]) -> Dict[str, Mapping[str, Any]]:
    return {item["id"]: item for item in truth.get("entities", [])}


def truth_relation_index(truth: Mapping[str, Any]) -> Dict[str, Mapping[str, Any]]:
    return {item["id"]: item for item in truth.get("relations", [])}


def all_truth_ids(truth: Mapping[str, Any]) -> Set[str]:
    result: Set[str] = set()
    for collection in ("entities", "instances", "relations", "equations"):
        for item in truth.get(collection, []):
            if isinstance(item, Mapping) and isinstance(item.get("id"), str):
                result.add(item["id"])
    return result


def relation_endpoint_pairs(relation: Mapping[str, Any]) -> List[Tuple[str, str]]:
    """Return stable source/target pairs for an authoritative relation."""
    output = relation.get("output")
    members = relation.get("members")
    if isinstance(output, str) and isinstance(members, list):
        return [(member, output) for member in members if isinstance(member, str)]
    source = relation.get("source")
    target = relation.get("target")
    if isinstance(source, str) and isinstance(target, str):
        return [(source, target)]
    if isinstance(source, list) and isinstance(target, str):
        return [(item, target) for item in source]
    if isinstance(source, str) and isinstance(target, list):
        return [(source, item) for item in target]
    return []


def node_ref_index(blueprint: Mapping[str, Any]) -> Dict[str, str]:
    """Map each truth instance reference to its containing blueprint node."""
    index: Dict[str, str] = {}
    for node in blueprint.get("nodes", []):
        for instance_ref in node.get("instance_refs", []):
            index[instance_ref] = node["id"]
    return index


def split_port_ref(value: str) -> Tuple[str, str]:
    if "." not in value:
        raise ArtifactError("port reference must be node.port: %s" % value)
    return tuple(value.rsplit(".", 1))  # type: ignore[return-value]


def compare_fingerprints(
    left: Mapping[str, Any], right: Mapping[str, Any]
) -> Dict[str, Any]:
    differences = [field for field in FINGERPRINT_FIELDS if left.get(field) != right.get(field)]
    four_core_equal = all(
        left.get(field) == right.get(field)
        for field in (
            "region_graph",
            "reading_axis",
            "stage_arrangement",
            "repetition_strategy",
        )
    )
    insufficient = four_core_equal and len(differences) < 3
    return {
        "categorical_differences": differences,
        "categorical_difference_count": len(differences),
        "core_fields_equal": four_core_equal,
        "occupied_area_distribution_left": left.get("occupied_area_distribution"),
        "occupied_area_distribution_right": right.get("occupied_area_distribution"),
        "sufficiently_different": not insufficient,
        "reason": (
            "different region graph/core layout or at least three categorical fields differ"
            if not insufficient
            else "same core layout and fewer than three categorical fields differ"
        ),
    }


def basic_truth_errors(truth: Mapping[str, Any]) -> List[str]:
    errors = require_fields(truth, "scientific_truth")
    for collection in ("entities", "instances", "relations", "equations"):
        items = truth.get(collection, [])
        if not isinstance(items, list):
            errors.append("%s must be a list" % collection)
            continue
        ids = [item.get("id") for item in items if isinstance(item, Mapping)]
        missing = [str(index) for index, value in enumerate(ids) if not value]
        if missing:
            errors.append("%s entries missing id at indices %s" % (collection, ",".join(missing)))
        duplicates = duplicate_values(value for value in ids if isinstance(value, str))
        if duplicates:
            errors.append("duplicate %s ids: %s" % (collection, ", ".join(duplicates)))

    instances = truth_instance_index(truth)
    for relation in truth.get("relations", []):
        for source, target in relation_endpoint_pairs(relation):
            if source not in instances:
                errors.append("relation %s has unknown source %s" % (relation.get("id"), source))
            if target not in instances:
                errors.append("relation %s has unknown target %s" % (relation.get("id"), target))
    return errors


def basic_blueprint_errors(
    blueprint: Mapping[str, Any], truth: Mapping[str, Any], rule_ids: Set[str]
) -> List[str]:
    errors = require_fields(blueprint, "candidate_blueprint")
    if blueprint.get("schema_version") == "1.1" and "depiction_policy" not in blueprint:
        errors.append("schema 1.1 blueprint requires depiction_policy")
    policy = blueprint.get("depiction_policy")
    if isinstance(policy, Mapping):
        required_policy_fields = {
            "relation_id", "depiction_mode", "semantic_scope", "visible_scope",
            "visible_instances", "semantic_multiplicity", "required_visual_sequence",
            "exact_instance_count_required_in_png", "exact_instance_count_required_in_svg",
            "caption_support",
        }
        missing = sorted(required_policy_fields - set(policy))
        if missing:
            errors.append("depiction_policy missing fields: %s" % ", ".join(missing))
        if policy.get("depiction_mode") not in {
            "literal_instances", "representative_template", "multiplicity_badge"
        }:
            errors.append("depiction_policy has unsupported depiction_mode")
    nodes = blueprint.get("nodes", [])
    edges = blueprint.get("edges", [])
    node_ids = [node.get("id") for node in nodes if isinstance(node, Mapping)]
    edge_ids = [edge.get("id") for edge in edges if isinstance(edge, Mapping)]
    duplicate_nodes = duplicate_values(value for value in node_ids if isinstance(value, str))
    duplicate_edges = duplicate_values(value for value in edge_ids if isinstance(value, str))
    if duplicate_nodes:
        errors.append("duplicate blueprint node ids: %s" % ", ".join(duplicate_nodes))
    if duplicate_edges:
        errors.append("duplicate blueprint edge ids: %s" % ", ".join(duplicate_edges))

    instances = truth_instance_index(truth)
    referenced: List[str] = []
    node_map = {node.get("id"): node for node in nodes if isinstance(node, Mapping)}
    for node in nodes:
        bbox = node.get("bbox")
        if not isinstance(bbox, list) or len(bbox) != 4:
            errors.append("node %s requires bbox [x,y,w,h]" % node.get("id"))
        for ref in node.get("instance_refs", []):
            referenced.append(ref)
            if ref not in instances:
                errors.append("node %s references unknown instance %s" % (node.get("id"), ref))
    duplicate_refs = duplicate_values(referenced)
    if duplicate_refs:
        errors.append("truth instances appear in multiple nodes: %s" % ", ".join(duplicate_refs))

    ports = blueprint.get("ports", [])
    port_ids = {port.get("id") for port in ports if isinstance(port, Mapping)}
    for edge in edges:
        for field in ("source", "target"):
            value = edge.get(field)
            if not isinstance(value, str):
                errors.append("edge %s missing %s port reference" % (edge.get("id"), field))
                continue
            try:
                node_id, port_name = split_port_ref(value)
            except ArtifactError as exc:
                errors.append(str(exc))
                continue
            if node_id not in node_map:
                errors.append("edge %s references unknown node %s" % (edge.get("id"), node_id))
            if "%s.%s" % (node_id, port_name) not in port_ids:
                errors.append("edge %s references undeclared port %s" % (edge.get("id"), value))

    for rule_id in blueprint.get("in_scope_rule_ids", []):
        if rule_id not in rule_ids:
            errors.append("blueprint references unknown rule id %s" % rule_id)
    return errors


def normalize_whitespace(value: str) -> str:
    return " ".join(value.split())
