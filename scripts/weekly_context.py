#!/usr/bin/env python3
"""Print context for an AI-assisted weekly work summary."""

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


def month_range(start: dt.date, end: dt.date) -> list[str]:
    months: list[str] = []
    current = dt.date(start.year, start.month, 1)
    stop = dt.date(end.year, end.month, 1)
    while current <= stop:
        months.append(current.strftime("%Y-%m"))
        if current.month == 12:
            current = dt.date(current.year + 1, 1, 1)
        else:
            current = dt.date(current.year, current.month + 1, 1)
    return months


def extract_log_entries(repo: Path, start: dt.date, end: dt.date) -> str:
    blocks: list[str] = []
    for month in month_range(start, end):
        path = repo / "ai-log" / f"{month}.md"
        if path.exists():
            blocks.append(f"## {path.relative_to(repo)}\n\n{path.read_text(encoding='utf-8').strip()}")
    return "\n\n".join(blocks) if blocks else "none"


def section(title: str, body: str) -> str:
    return f"## {title}\n\n```text\n{body.strip() or 'none'}\n```"


def main() -> int:
    today = dt.date.today()
    default_since = today - dt.timedelta(days=7)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=".", help="Repository to summarize")
    parser.add_argument("--since", default=default_since.isoformat(), help="Start date YYYY-MM-DD")
    parser.add_argument("--until", default=today.isoformat(), help="End date YYYY-MM-DD")
    args = parser.parse_args()

    repo = git_root(Path(args.repo).resolve())
    since = dt.date.fromisoformat(args.since)
    until = dt.date.fromisoformat(args.until)

    git_log = run_git(
        repo,
        "log",
        f"--since={since.isoformat()} 00:00",
        f"--until={until.isoformat()} 23:59",
        "--pretty=format:%h %ad %s",
        "--date=short",
    )
    diff_stat = run_git(repo, "diff", "--stat")
    status = run_git(repo, "status", "--short")

    print("# AI Weekly Summary Context")
    print()
    print(f"- repo: `{repo}`")
    print(f"- range: `{since.isoformat()}..{until.isoformat()}`")
    print()
    print(section("Git Commits", git_log))
    print()
    print(section("Working Tree Status", status))
    print()
    print(section("Tracked Working Tree Diff Stat", diff_stat))
    print()
    print("## AI Worklog Entries")
    print()
    print(extract_log_entries(repo, since, until))
    return 0


if __name__ == "__main__":
    sys.exit(main())
