#!/usr/bin/env python3
"""Draft an AI worklog entry from recent git context."""

from __future__ import annotations

import argparse
import datetime as dt
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


def uniq_lines(*blocks: str) -> list[str]:
    values: list[str] = []
    for block in blocks:
        for line in block.splitlines():
            if line and line not in values:
                values.append(line)
    return values


def bullet(items: list[str], fallback: str = "Not specified.") -> str:
    values = [item for item in items if item]
    if not values:
        values = [fallback]
    return "\n".join(f"- {item}" for item in values)


def main() -> int:
    today = dt.date.today().isoformat()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=".", help="Repository to inspect")
    parser.add_argument("--since", default="HEAD~1", help="Ref/date for commit context")
    parser.add_argument("--title", default="Draft task title")
    parser.add_argument("--goal", default="Draft one-sentence goal.")
    parser.add_argument("--privacy", choices=["public", "project", "private"], default="project")
    args = parser.parse_args()

    repo = git_root(Path(args.repo).resolve())
    branch = run_git(repo, "branch", "--show-current") or "detached"
    head = run_git(repo, "log", "-1", "--pretty=format:%h %s")
    status = run_git(repo, "status", "--short")
    recent = run_git(repo, "log", f"{args.since}..HEAD", "--pretty=format:%h %s")
    if not recent:
        recent = run_git(repo, "log", "-5", "--pretty=format:%h %s")
    diff_stat = run_git(repo, "diff", "--stat")
    staged_stat = run_git(repo, "diff", "--cached", "--stat")
    files = uniq_lines(
        run_git(repo, "diff", "--name-only"),
        run_git(repo, "diff", "--cached", "--name-only"),
        run_git(repo, "ls-files", "--others", "--exclude-standard"),
        run_git(repo, "show", "--name-only", "--pretty=format:", "HEAD"),
    )

    print(f"# AI Worklog Draft - {today}")
    print()
    print(f"- repo: `{repo}`")
    print(f"- branch: `{branch}`")
    print(f"- head: `{head or 'none'}`")
    print()
    print("## Draft Entry")
    print()
    print(f"## {today} - {args.title}")
    print()
    print(f"Goal: {args.goal}")
    print()
    print("Changed:")
    print("- TODO: rewrite from git context below.")
    print()
    print("Artifacts:")
    print(f"- commit: {head.split(' ', 1)[0] if head and not status else 'pending'}")
    print(f"- files: {', '.join(files) if files else 'none'}")
    print(f"- privacy: {args.privacy}")
    print()
    print("Decision:")
    print("- Optional. Add only if there was a durable decision.")
    print()
    print("Pitfall:")
    print("- Optional. Add only if there was a reusable lesson.")
    print()
    print("## Git Context")
    print()
    print("### Status")
    print("```text")
    print(status or "none")
    print("```")
    print()
    print("### Recent Commits")
    print("```text")
    print(recent or "none")
    print("```")
    print()
    print("### Diff Stat")
    print("```text")
    print("\n\n".join(block for block in [diff_stat, staged_stat] if block) or "none")
    print("```")
    print()
    print("### Files")
    print(bullet(files, "none"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
