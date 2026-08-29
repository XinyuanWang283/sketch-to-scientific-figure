#!/usr/bin/env python3
"""Release-boundary checks for the public repository."""

from __future__ import annotations

import re
import subprocess
import unittest
from pathlib import Path
from urllib.parse import unquote


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
TEXT_SUFFIXES = {
    ".cff", ".css", ".html", ".js", ".json", ".md", ".mjs", ".py",
    ".svg", ".tex", ".toml", ".txt", ".yaml", ".yml",
}


def public_repository_files() -> list[Path]:
    """Return tracked and release-candidate files, excluding ignored local state."""
    result = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        cwd=REPOSITORY_ROOT,
        capture_output=True,
        check=False,
    )
    if result.returncode == 0:
        paths = [
            REPOSITORY_ROOT / value.decode("utf-8")
            for value in result.stdout.split(b"\0")
            if value
        ]
        return [path for path in paths if path.is_symlink() or path.is_file()]

    # Source distributions and exported snapshots may not contain .git.
    ignored_directory_names = {
        ".git", ".mypy_cache", ".pytest_cache", ".ruff_cache", ".tox",
        ".venv", "__pycache__", "build", "dist", "venv",
    }
    return [
        path
        for path in REPOSITORY_ROOT.rglob("*")
        if (path.is_symlink() or path.is_file())
        and not ignored_directory_names.intersection(path.relative_to(REPOSITORY_ROOT).parts)
    ]


def public_text_files() -> list[Path]:
    return [
        path
        for path in public_repository_files()
        if not path.is_symlink() and path.suffix.lower() in TEXT_SUFFIXES
    ]


class PublicRepositoryTests(unittest.TestCase):
    def test_runtime_requirements_match_project_metadata(self) -> None:
        pyproject = (REPOSITORY_ROOT / "pyproject.toml").read_text(encoding="utf-8")
        dependency_block = re.search(
            r"(?ms)^dependencies\s*=\s*\[(.*?)^\]",
            pyproject,
        )
        self.assertIsNotNone(dependency_block)
        declared = re.findall(r'"([^"]+)"', dependency_block.group(1))  # type: ignore[union-attr]
        requirements = [
            line.strip()
            for line in (REPOSITORY_ROOT / "requirements.txt").read_text(
                encoding="utf-8"
            ).splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        ]
        self.assertEqual(requirements, declared)

    def test_active_v01_entry_points_use_canonical_case_and_honest_call_wording(self) -> None:
        canonical_case_entry_points = [
            Path("README.md"),
            Path("START_HERE_\u4e2d\u6587.md"),
            Path(".agents/skills/sketch-to-scientific-figure/SKILL.md"),
            Path("prompts/02_selected_proposal_to_svg.md"),
            Path("examples/deep_image_prior/README.md"),
            Path("examples/deep_image_prior/reference_case_v0_1.md"),
            Path("docs/science-day-demo.md"),
            Path("docs/release_checklist.md"),
            Path("docs/technical_reference.md"),
        ]
        active_entry_points = canonical_case_entry_points + [
            Path("prompts/01_sketch_to_five_proposals.md"),
        ]
        forbidden_independence_claims = [
            "five independent imagegen",
            "five independently generated",
            "independent built-in imagegen",
            "independent codex imagegen",
            "calls are independent",
            "created_after_independent_generation",
        ]

        problems = []
        for relative_path in active_entry_points:
            text = (REPOSITORY_ROOT / relative_path).read_text(encoding="utf-8")
            lowered = text.lower()
            if (
                relative_path in canonical_case_entry_points
                and "fidelity_v2" not in text
                and "fidelity-v2" not in lowered
            ):
                problems.append(f"{relative_path} does not identify fidelity-v2")
            for claim in forbidden_independence_claims:
                if claim in lowered:
                    problems.append(f"{relative_path} contains unsupported wording: {claim}")

            for line_number, line in enumerate(text.splitlines(), start=1):
                if "editable_delivery_c_region_fidelity" in line and not {
                    "legacy", "earlier", "histor"
                }.intersection(line.lower().split()):
                    problems.append(
                        f"{relative_path}:{line_number} presents the legacy delivery as active"
                    )

        self.assertEqual(problems, [])

    def test_no_local_absolute_paths_or_cache_artifacts(self) -> None:
        local_prefixes = [
            "/" + "Users" + "/",
            "/" + "home" + "/",
            "/" + "private" + "/" + "tmp" + "/",
            "/" + "var" + "/" + "folders" + "/",
        ]
        path_problems = []
        for path in public_text_files():
            text = path.read_text(encoding="utf-8", errors="replace")
            for prefix in local_prefixes:
                if prefix in text:
                    path_problems.append("%s contains %s" % (path.relative_to(REPOSITORY_ROOT), prefix))
        self.assertEqual(path_problems, [])

        forbidden_names = {".DS_Store", ".pytest_cache", "__pycache__"}
        artifacts = [
            str(path.relative_to(REPOSITORY_ROOT))
            for path in public_repository_files()
            if forbidden_names.intersection(path.relative_to(REPOSITORY_ROOT).parts)
            or path.suffix == ".pyc"
            or any(part.endswith(".egg-info") for part in path.relative_to(REPOSITORY_ROOT).parts)
        ]
        self.assertEqual(artifacts, [])

    def test_release_files_are_regular_contained_paths(self) -> None:
        root = REPOSITORY_ROOT.resolve()
        problems = []
        for path in public_repository_files():
            relative = path.relative_to(REPOSITORY_ROOT)
            if path.is_symlink():
                problems.append(f"{relative} is a symbolic link")
                continue
            try:
                path.resolve(strict=True).relative_to(root)
            except (OSError, ValueError):
                problems.append(f"{relative} escapes the repository or is missing")
        self.assertEqual(problems, [])

    def test_no_withheld_case_indicators_in_public_paths_or_text(self) -> None:
        indicators = (
            "Progressive" + " Unbinning",
            "progressive" + "_unbinning",
            "progressive" + "-unbinning",
            "private" + "-pu-unpublished-2026-08-23",
        )
        problems = []
        for path in public_repository_files():
            relative = path.relative_to(REPOSITORY_ROOT).as_posix()
            for indicator in indicators:
                if indicator.lower() in relative.lower():
                    problems.append(f"{relative} contains a withheld case indicator")
        for path in public_text_files():
            text = path.read_text(encoding="utf-8", errors="replace")
            for indicator in indicators:
                if indicator.lower() in text.lower():
                    problems.append(
                        f"{path.relative_to(REPOSITORY_ROOT)} contains a withheld case indicator"
                    )
        self.assertEqual(problems, [])

    def test_local_markdown_links_resolve(self) -> None:
        link_pattern = re.compile(r"(?<!!)\[[^\]]*\]\(([^)]+)\)")
        image_pattern = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")
        problems = []
        for markdown in (path for path in public_text_files() if path.suffix.lower() == ".md"):
            text = markdown.read_text(encoding="utf-8")
            links = link_pattern.findall(text) + image_pattern.findall(text)
            for raw_target in links:
                target = raw_target.strip().split(maxsplit=1)[0].strip("<>")
                if not target or target.startswith(("#", "http://", "https://", "mailto:")):
                    continue
                relative = unquote(target.split("#", 1)[0])
                if not relative:
                    continue
                resolved = (markdown.parent / relative).resolve()
                try:
                    resolved.relative_to(REPOSITORY_ROOT.resolve())
                except ValueError:
                    problems.append(
                        "%s -> %s escapes repository"
                        % (markdown.relative_to(REPOSITORY_ROOT), target)
                    )
                    continue
                if not resolved.exists():
                    problems.append("%s -> %s" % (markdown.relative_to(REPOSITORY_ROOT), target))
        self.assertEqual(problems, [])


if __name__ == "__main__":
    unittest.main()
