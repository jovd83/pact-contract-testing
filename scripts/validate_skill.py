#!/usr/bin/env python3
"""Repository-local validation for the pact-contract-testing skill family.

Validates the core skill plus every language pack under languages/, and checks the
standard repo files. Exit 0 = pass, 1 = failures found. Stdlib only.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT_REQUIRED_FILES = [
    "SKILL.md",
    "README.md",
    "CHANGELOG.md",
    "LICENSE",
    "agents/openai.yaml",
    "evals/evals.json",
    "references/languages.md",
    "references/matchers-and-states.md",
    "references/derivation-modes.md",
    "references/schema-driven.md",
    "references/broker-and-cicd.md",
    "references/advanced-features.md",
    "scripts/scaffold_from_schema.py",
    "scripts/publish_pacts.sh",
    "scripts/can_i_deploy.sh",
]

EXPECTED_LANGUAGE_PACKS = {
    "java", "javascript", "dotnet", "go", "python",
    "ruby", "php", "rust", "swift", "scala", "cpp",
}

CORE_REQUIRED_SECTIONS = [
    "# Pact Contract Testing",
    "## Scope",
    "## Core mental model",
    "## Required inputs",
    "## Decision tree",
    "## Workflow",
    "## Language support",
    "## Anti-patterns to refuse",
    "## Troubleshooting",
    "## Final response contract",
]


def parse_frontmatter(content: str) -> tuple[dict[str, str], str | None]:
    if not content.startswith("---\n"):
        return {}, "must start with YAML frontmatter"
    try:
        _, fm, _ = content.split("---\n", 2)
    except ValueError:
        return {}, "frontmatter must be closed with ---"
    values: dict[str, str] = {}
    for line in fm.splitlines():
        if not line.strip() or line[0] in " \t":
            continue
        m = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
        if m:
            values[m.group(1)] = m.group(2).strip().strip('"')
    return values, None


def validate_skill_md(path: Path, errors: list[str], warnings: list[str], names: dict[str, Path],
                      expected_name: str | None = None) -> None:
    rel = path.as_posix()
    fm, err = parse_frontmatter(path.read_text(encoding="utf-8"))
    if err:
        errors.append(f"{rel}: {err}")
        return
    name = fm.get("name", "")
    desc = fm.get("description", "")
    if not re.fullmatch(r"[a-z0-9-]{1,64}", name):
        errors.append(f"{rel}: name '{name}' must be lowercase hyphen-case (1-64 chars)")
    if expected_name and name != expected_name:
        errors.append(f"{rel}: name must be '{expected_name}', got '{name}'")
    if name in names:
        errors.append(f"{rel}: duplicate skill name '{name}' (also in {names[name].as_posix()})")
    elif name:
        names[name] = path
    if not desc:
        errors.append(f"{rel}: description is required")
    if len(desc) > 1024:
        errors.append(f"{rel}: description must be <= 1024 chars (is {len(desc)})")
    if "<" in desc or ">" in desc:
        errors.append(f"{rel}: description must not contain angle brackets")
    if fm.get("license", "").upper() != "MIT":
        warnings.append(f"{rel}: license should be MIT")
    if not desc.startswith("Use when"):
        warnings.append(f"{rel}: description should start with 'Use when' (discovery convention)")


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    errors: list[str] = []
    warnings: list[str] = []
    names: dict[str, Path] = {}

    # Root files
    for rel in ROOT_REQUIRED_FILES:
        if not (root / rel).exists():
            errors.append(f"missing required file: {rel}")

    # Core skill
    core = root / "SKILL.md"
    if core.exists():
        validate_skill_md(core, errors, warnings, names, expected_name="pact-contract-testing")
        content = core.read_text(encoding="utf-8")
        for sec in CORE_REQUIRED_SECTIONS:
            if sec not in content:
                errors.append(f"SKILL.md missing required section: {sec}")

    # Language packs
    langs_dir = root / "languages"
    found_packs: set[str] = set()
    if langs_dir.is_dir():
        for sub in sorted(p for p in langs_dir.iterdir() if p.is_dir()):
            found_packs.add(sub.name)
            pack = sub / "SKILL.md"
            if not pack.exists():
                errors.append(f"languages/{sub.name}: missing SKILL.md")
                continue
            validate_skill_md(pack, errors, warnings, names)
    else:
        errors.append("missing languages/ directory")

    missing_packs = EXPECTED_LANGUAGE_PACKS - found_packs
    if missing_packs:
        errors.append(f"missing language packs: {', '.join(sorted(missing_packs))}")

    # Report
    total_skills = len(names)
    print(f"pact-contract-testing validation @ {root}")
    print(f"  skills validated: {total_skills} (1 core + {len(found_packs)} language packs)")
    for w in warnings:
        print(f"  WARN: {w}")
    if errors:
        for e in errors:
            print(f"  FAIL: {e}")
        print(f"RESULT: FAIL ({len(errors)} error(s), {len(warnings)} warning(s))")
        return 1
    print(f"RESULT: PASS ({len(warnings)} warning(s))")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
