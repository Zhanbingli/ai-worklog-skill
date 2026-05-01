#!/usr/bin/env python3
"""Collect git context for an AI worklog entry."""

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


def section(title: str, body: str) -> str:
    body = body.strip() or "none"
    return f"### {title}\n\n```text\n{body}\n```"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=".", help="Repository path")
    parser.add_argument(
        "--since",
        default=None,
        help="Optional commit/ref to diff against for completed work context",
    )
    args = parser.parse_args()

    repo = git_root(Path(args.repo).resolve())
    today = dt.datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %z")
    branch = run_git(repo, "branch", "--show-current") or "detached"
    head = run_git(repo, "log", "-1", "--pretty=format:%h %s")
    status = run_git(repo, "status", "--short")

    if args.since:
        diff_stat = run_git(repo, "diff", "--stat", f"{args.since}..HEAD")
        changed_files = run_git(repo, "diff", "--name-only", f"{args.since}..HEAD")
    else:
        diff_stat = run_git(repo, "diff", "--stat")
        changed_files = run_git(repo, "diff", "--name-only")
    staged_stat = run_git(repo, "diff", "--cached", "--stat")
    staged_files = run_git(repo, "diff", "--cached", "--name-only")
    untracked_files = run_git(repo, "ls-files", "--others", "--exclude-standard")
    if staged_stat:
        diff_stat = f"{diff_stat}\n\nStaged:\n{staged_stat}".strip()
    changed_files = "\n".join(
        item
        for item in [changed_files, staged_files, untracked_files]
        if item.strip()
    )

    print(f"# AI Worklog Context\n")
    print(f"- repo: `{repo}`")
    print(f"- captured_at: `{today}`")
    print(f"- branch: `{branch}`")
    print(f"- head: `{head or 'none'}`")
    print(f"- since: `{args.since or 'working tree'}`")
    print()
    print(section("Status", status))
    print()
    print(section("Diff Stat", diff_stat))
    print()
    print(section("Changed Files", changed_files))
    return 0


if __name__ == "__main__":
    sys.exit(main())
