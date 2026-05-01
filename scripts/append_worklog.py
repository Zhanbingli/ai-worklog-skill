#!/usr/bin/env python3
"""Append a standard personal AI worklog entry to ai-log/YYYY-MM.md."""

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


def current_commit(repo: Path) -> str:
    if run_git(repo, "status", "--short"):
        return "pending"
    return run_git(repo, "log", "-1", "--pretty=format:%h") or "pending"


def changed_files(repo: Path) -> list[str]:
    candidates = [
        run_git(repo, "diff", "--name-only"),
        run_git(repo, "diff", "--cached", "--name-only"),
        run_git(repo, "ls-files", "--others", "--exclude-standard"),
    ]
    files: list[str] = []
    for block in candidates:
        for line in block.splitlines():
            if line and line not in files:
                files.append(line)
    if files:
        return files

    last_commit_files = run_git(repo, "show", "--name-only", "--pretty=format:", "HEAD")
    return [line for line in last_commit_files.splitlines() if line]


def bullet_lines(items: list[str], fallback: str = "Not specified.") -> str:
    values = [item.strip() for item in items if item.strip()]
    if not values:
        values = [fallback]
    return "\n".join(f"- {item}" for item in values)


def build_entry(args: argparse.Namespace, repo: Path) -> str:
    files = args.file or changed_files(repo)
    commit = args.commit or current_commit(repo)

    lines = [
        f"## {args.date} - {args.title}",
        "",
        f"Goal: {args.goal or 'Not specified.'}",
        "",
        "Changed:",
        bullet_lines(args.changed),
        "",
        "Artifacts:",
        f"- commit: {commit}",
        f"- files: {', '.join(files) if files else 'none'}",
        f"- privacy: {args.privacy}",
    ]
    if args.decision:
        lines.extend(["", "Decision:", bullet_lines(args.decision)])
    if args.pitfall:
        lines.extend(["", "Pitfall:", bullet_lines(args.pitfall)])
    if args.next:
        lines.extend(["", "Next:", bullet_lines(args.next)])
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    today = dt.date.today().isoformat()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=".", help="Repository to log work for")
    parser.add_argument("--title", required=True, help="Short task title")
    parser.add_argument("--goal", default="", help="One-sentence task goal")
    parser.add_argument("--changed", action="append", default=[], help="Changed item")
    parser.add_argument("--decision", action="append", default=[], help="Decision item")
    parser.add_argument("--pitfall", action="append", default=[], help="Pitfall item")
    parser.add_argument("--next", action="append", default=[], help="Follow-up item")
    parser.add_argument("--file", action="append", default=[], help="Artifact file path")
    parser.add_argument("--commit", default="", help="Commit sha, or pending")
    parser.add_argument(
        "--privacy",
        choices=["public", "project", "private"],
        default="project",
        help="Visibility label for this entry",
    )
    parser.add_argument("--date", default=today, help="Entry date as YYYY-MM-DD")
    parser.add_argument("--log-dir", default="ai-log", help="Worklog directory")
    parser.add_argument("--dry-run", action="store_true", help="Print entry without writing")
    args = parser.parse_args()

    repo = git_root(Path(args.repo).resolve())
    entry = build_entry(args, repo)
    month = args.date[:7]
    path = repo / args.log_dir / f"{month}.md"

    if args.dry_run:
        print(entry)
        return 0

    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(f"# {month} AI Worklog\n\n", encoding="utf-8")
    with path.open("a", encoding="utf-8") as handle:
        handle.write(entry)
        handle.write("\n")
    print(path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
