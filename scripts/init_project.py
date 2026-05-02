#!/usr/bin/env python3
"""Initialize a repository for AI worklog usage."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path


def run_git(repo: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", "-C", str(repo), *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if proc.returncode != 0:
        return ""
    return proc.stdout.strip()


def git_root(repo: Path) -> Path:
    root = run_git(repo, "rev-parse", "--show-toplevel")
    if not root:
        raise SystemExit(f"Not a git repository: {repo}")
    return Path(root)


def ensure_gitignore_entry(path: Path, entry: str, dry_run: bool) -> bool:
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    lines = existing.splitlines()
    if entry.rstrip("/") in {line.rstrip("/") for line in lines}:
        return False
    if dry_run:
        return True
    suffix = "" if not existing or existing.endswith("\n") else "\n"
    path.write_text(f"{existing}{suffix}{entry}\n", encoding="utf-8")
    return True


def write_file_once(path: Path, content: str, dry_run: bool) -> bool:
    if path.exists():
        return False
    if not dry_run:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    return True


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9._/-]+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-")
    return value or "unknown"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=".", help="Repository to initialize")
    parser.add_argument("--project", default="", help="Project slug for log directories")
    parser.add_argument("--remote", default="", help="Remote worklog repository to store in .ai-worklog.json")
    parser.add_argument("--tag", action="append", default=[], help="Default tag to write into .ai-worklog.json")
    parser.add_argument("--no-config", action="store_true", help="Do not write .ai-worklog.json")
    parser.add_argument("--dry-run", action="store_true", help="Print planned changes")
    args = parser.parse_args()

    repo = git_root(Path(args.repo).resolve())
    project = slugify(args.project or repo.name)
    planned: list[str] = []

    for directory in ["ai-log", "ai-memory", f"ai-log/{project}", f"ai-memory/{project}", ".ai-raw"]:
        path = repo / directory
        if not path.exists():
            planned.append(f"create directory: {directory}/")
            if not args.dry_run:
                path.mkdir(parents=True, exist_ok=True)

    memory_files = {
        "decisions.md": f"# AI Project Decisions - {project}\n\n",
        "pitfalls.md": f"# AI Project Pitfalls - {project}\n\n",
        "prompts.md": f"# Reusable AI Prompt Patterns - {project}\n\n",
    }
    for filename, content in memory_files.items():
        path = repo / "ai-memory" / project / filename
        if write_file_once(path, content, args.dry_run):
            planned.append(f"create file: ai-memory/{project}/{filename}")

    if ensure_gitignore_entry(repo / ".gitignore", ".ai-raw/", args.dry_run):
        planned.append("add .ai-raw/ to .gitignore")

    config_path = repo / ".ai-worklog.json"
    if not args.no_config and not config_path.exists():
        config = {
            "project": project,
            "remote": args.remote,
            "default_tags": args.tag,
        }
        planned.append("create file: .ai-worklog.json")
        if not args.dry_run:
            config_path.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if planned:
        print("\n".join(planned))
    else:
        print("AI worklog project files already initialized.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
