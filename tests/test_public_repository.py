#!/usr/bin/env python3
"""Release-boundary checks for the public repository."""

from __future__ import annotations

import re
import unittest
from pathlib import Path
from urllib.parse import unquote


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
TEXT_SUFFIXES = {
    ".cff", ".css", ".html", ".js", ".json", ".md", ".mjs", ".py",
    ".svg", ".tex", ".toml", ".txt", ".yaml", ".yml",
}


def public_text_files() -> list[Path]:
    return [
        path
        for path in REPOSITORY_ROOT.rglob("*")
        if path.is_file()
        and path.suffix.lower() in TEXT_SUFFIXES
        and ".git" not in path.parts
        and "__pycache__" not in path.parts
    ]


class PublicRepositoryTests(unittest.TestCase):
    def test_unpublished_case_identifiers_are_absent(self) -> None:
        withheld_identifiers = [
            "progressive" + "_unbinning",
            "progressive" + "-unbinning",
            "progressive" + " unbinning",
        ]
        problems = []
        for path in public_text_files():
            text = path.read_text(encoding="utf-8", errors="replace").lower()
            for identifier in withheld_identifiers:
                if identifier in text:
                    problems.append("%s contains %s" % (path.relative_to(REPOSITORY_ROOT), identifier))
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
            for path in REPOSITORY_ROOT.rglob("*")
            if path.name in forbidden_names or path.suffix == ".pyc"
        ]
        self.assertEqual(artifacts, [])

    def test_local_markdown_links_resolve(self) -> None:
        link_pattern = re.compile(r"(?<!!)\[[^\]]*\]\(([^)]+)\)")
        image_pattern = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")
        problems = []
        for markdown in REPOSITORY_ROOT.rglob("*.md"):
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
                if not resolved.exists():
                    problems.append("%s -> %s" % (markdown.relative_to(REPOSITORY_ROOT), target))
        self.assertEqual(problems, [])


if __name__ == "__main__":
    unittest.main()
