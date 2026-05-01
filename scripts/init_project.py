#!/usr/bin/env python3
"""Initialize a repository for AI worklog usage."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


MEMORY_FILES = {
    "decisions.md": "# AI Project Decisions\n\n",
    "pitfalls.md": "# AI Project Pitfalls\n\n",
    "prompts.md": "# Reusable AI Prompt Patterns\n\n",
}


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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=".", help="Repository to initialize")
    parser.add_argument("--dry-run", action="store_true", help="Print planned changes")
    args = parser.parse_args()

    repo = git_root(Path(args.repo).resolve())
    planned: list[str] = []

    for directory in ["ai-log", "ai-memory", ".ai-raw"]:
        path = repo / directory
        if not path.exists():
            planned.append(f"create directory: {directory}/")
            if not args.dry_run:
                path.mkdir(parents=True, exist_ok=True)

    for filename, content in MEMORY_FILES.items():
        path = repo / "ai-memory" / filename
        if write_file_once(path, content, args.dry_run):
            planned.append(f"create file: ai-memory/{filename}")

    if ensure_gitignore_entry(repo / ".gitignore", ".ai-raw/", args.dry_run):
        planned.append("add .ai-raw/ to .gitignore")

    if planned:
        print("\n".join(planned))
    else:
        print("AI worklog project files already initialized.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
