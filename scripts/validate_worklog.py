#!/usr/bin/env python3
"""Validate AI worklog structure without requiring third-party YAML packages."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

from ai_worklog.common import iter_markdown_entries, slugify, split_frontmatter_block


REQUIRED_FIELDS = ["id", "date", "project", "tags", "privacy", "commit", "files"]
REQUIRED_BODY_MARKERS = ["Goal:", "Changed:", "Artifacts:"]


def is_list(value: object) -> bool:
    return isinstance(value, list) and all(isinstance(item, str) for item in value)


def validate_entry(path: Path, block: str) -> list[str]:
    errors: list[str] = []
    meta, body = split_frontmatter_block(block)
    if not meta:
        return [f"{path}: entry is missing YAML frontmatter"]

    for field in REQUIRED_FIELDS:
        if field not in meta:
            errors.append(f"{path}: missing frontmatter field `{field}`")

    date = str(meta.get("date", ""))
    try:
        dt.date.fromisoformat(date)
    except ValueError:
        errors.append(f"{path}: invalid date `{date}`")

    project = str(meta.get("project", ""))
    if project and project != slugify(project):
        errors.append(f"{path}: project `{project}` is not a stable slug")

    if meta.get("privacy") not in {"public", "project", "private"}:
        errors.append(f"{path}: privacy must be public, project, or private")

    for field in ["tags", "files"]:
        if field in meta and not is_list(meta[field]):
            errors.append(f"{path}: `{field}` must be a YAML list")

    if "## " not in body:
        errors.append(f"{path}: entry body is missing a level-2 title")
    for marker in REQUIRED_BODY_MARKERS:
        if marker not in body:
            errors.append(f"{path}: entry body is missing `{marker}`")

    parts = path.parts
    if "ai-log" in parts:
        index = parts.index("ai-log")
        if len(parts) > index + 2:
            path_project = parts[index + 1]
            if project and path_project != project:
                errors.append(f"{path}: path project `{path_project}` does not match frontmatter project `{project}`")
        if date and not path.name.startswith(date[:7]):
            errors.append(f"{path}: file month does not match entry date `{date}`")

    return errors


def validate_logs(repo: Path) -> list[str]:
    errors: list[str] = []
    for path in sorted((repo / "ai-log").glob("*/*.md")):
        text = path.read_text(encoding="utf-8")
        entries = iter_markdown_entries(text)
        if not entries:
            errors.append(f"{path}: no frontmatter entries found")
            continue
        for block in entries:
            errors.extend(validate_entry(path, block))
    return errors


def validate_memory(repo: Path) -> list[str]:
    errors: list[str] = []
    for path in sorted((repo / "ai-memory").glob("*/*.md")):
        text = path.read_text(encoding="utf-8")
        if path.name in {"decisions.md", "pitfalls.md"} and "## " in text and "Project:" not in text:
            errors.append(f"{path}: memory file should include Project: fields for retrieval")
    return errors


def validate_indexes(repo: Path) -> list[str]:
    errors: list[str] = []
    for path in sorted((repo / "ai-index").glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"{path}: invalid JSON: {exc}")
            continue
        project = path.stem
        if data.get("project") != project:
            errors.append(f"{path}: index project does not match filename")
        latest = data.get("latest_entries", [])
        if latest and not isinstance(latest, list):
            errors.append(f"{path}: latest_entries must be a list")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=".", help="Worklog repository or project repository to validate")
    parser.add_argument("--skip-memory", action="store_true", help="Skip ai-memory checks")
    parser.add_argument("--skip-index", action="store_true", help="Skip ai-index checks")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    errors = validate_logs(repo)
    if not args.skip_memory:
        errors.extend(validate_memory(repo))
    if not args.skip_index:
        errors.extend(validate_indexes(repo))

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print("AI worklog structure is valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
