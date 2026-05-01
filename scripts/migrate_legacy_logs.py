#!/usr/bin/env python3
"""Copy old global AI worklog files into project-scoped directories."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from ai_worklog.common import slugify


def split_sections(text: str) -> tuple[str, list[str]]:
    header: list[str] = []
    sections: list[str] = []
    current: list[str] = []
    seen_section = False
    for line in text.splitlines():
        if line.startswith("## "):
            seen_section = True
            if current:
                sections.append("\n".join(current).strip())
            current = [line]
        elif seen_section:
            current.append(line)
        else:
            header.append(line)
    if current:
        sections.append("\n".join(current).strip())
    return "\n".join(header).strip(), [section for section in sections if section]


def section_project(section: str, default: str) -> str:
    match = re.search(r"(?im)^-\s*project:\s*(.+)$|^project:\s*(.+)$", section)
    if not match:
        return default
    value = next(item for item in match.groups() if item)
    return slugify(value)


def append_once(path: Path, title: str, section: str, dry_run: bool) -> bool:
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    if section in existing:
        return False
    if dry_run:
        return True
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(f"{title}\n\n", encoding="utf-8")
    with path.open("a", encoding="utf-8") as handle:
        handle.write(section.rstrip())
        handle.write("\n\n")
    return True


def migrate_logs(repo: Path, default_project: str, dry_run: bool) -> list[str]:
    actions: list[str] = []
    for path in sorted((repo / "ai-log").glob("*.md")):
        month = path.stem
        _, sections = split_sections(path.read_text(encoding="utf-8"))
        for section in sections:
            project = section_project(section, default_project)
            target = repo / "ai-log" / project / f"{month}.md"
            if append_once(target, f"# {month} AI Worklog - {project}", section, dry_run):
                actions.append(f"{path.relative_to(repo)} -> {target.relative_to(repo)}")
    return actions


def migrate_memory(repo: Path, default_project: str, dry_run: bool) -> list[str]:
    actions: list[str] = []
    for path in [repo / "ai-memory" / name for name in ["decisions.md", "pitfalls.md", "prompts.md"]]:
        if not path.exists():
            continue
        _, sections = split_sections(path.read_text(encoding="utf-8"))
        for section in sections:
            project = section_project(section, default_project)
            target = repo / "ai-memory" / project / path.name
            title = f"# AI Project {path.stem.title()} - {project}"
            if append_once(target, title, section, dry_run):
                actions.append(f"{path.relative_to(repo)} -> {target.relative_to(repo)}")
    return actions


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=".", help="Worklog repository to migrate")
    parser.add_argument("--default-project", default="global", help="Project slug for unscoped legacy sections")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    actions = migrate_logs(repo, slugify(args.default_project), args.dry_run)
    actions.extend(migrate_memory(repo, slugify(args.default_project), args.dry_run))
    if actions:
        print("\n".join(actions))
    else:
        print("No legacy entries needed migration.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
