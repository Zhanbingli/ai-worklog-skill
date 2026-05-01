#!/usr/bin/env python3
"""Publish a sanitized AI worklog entry to a remote GitHub repository.

The script clones the remote into a temporary directory, writes only the
worklog/memory files, pushes the commit, and removes the temporary directory.
"""

from __future__ import annotations

import argparse
import datetime as dt
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import scan_secrets


DEFAULT_REMOTE = "https://github.com/Zhanbingli/ai-worklog.git"


def run(cmd: list[str], cwd: Path | None = None, check: bool = True) -> str:
    proc = subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if check and proc.returncode != 0:
        detail = proc.stderr.strip() or proc.stdout.strip()
        raise SystemExit(f"Command failed: {' '.join(cmd)}\n{detail}")
    return proc.stdout.strip()


def bullet_lines(items: list[str], fallback: str = "Not specified.") -> str:
    values = [item.strip() for item in items if item.strip()]
    if not values:
        values = [fallback]
    return "\n".join(f"- {item}" for item in values)


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9._/-]+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-")
    return value or "unknown"


def append(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(text)
        if not text.endswith("\n"):
            handle.write("\n")


def ensure_base(repo: Path) -> None:
    (repo / "ai-log").mkdir(parents=True, exist_ok=True)
    (repo / "ai-memory").mkdir(parents=True, exist_ok=True)
    gitignore = repo / ".gitignore"
    existing = gitignore.read_text(encoding="utf-8") if gitignore.exists() else ""
    if ".ai-raw/" not in existing.splitlines():
        suffix = "" if not existing or existing.endswith("\n") else "\n"
        gitignore.write_text(f"{existing}{suffix}.ai-raw/\n", encoding="utf-8")
    readme = repo / "README.md"
    if not readme.exists():
        readme.write_text(
            "# AI Worklog\n\n"
            "Public-safe records of AI-assisted work. Raw transcripts, secrets, "
            "private data, and audit logs are not stored here.\n",
            encoding="utf-8",
        )
    for name, title in [
        ("decisions.md", "# AI Project Decisions\n\n"),
        ("pitfalls.md", "# AI Project Pitfalls\n\n"),
        ("prompts.md", "# Reusable AI Prompt Patterns\n\n"),
    ]:
        path = repo / "ai-memory" / name
        if not path.exists():
            path.write_text(title, encoding="utf-8")


def build_log_entry(args: argparse.Namespace) -> str:
    files = ", ".join(args.file) if args.file else "none"
    lines = [
        f"## {args.date} - {args.title}",
        "",
        f"Goal: {args.goal or 'Not specified.'}",
        "",
        "Changed:",
        bullet_lines(args.changed),
        "",
        "Artifacts:",
        f"- project: {args.project}",
        f"- tags: {', '.join(args.tag) if args.tag else 'none'}",
        f"- commit: {args.artifact_commit or 'pending'}",
        f"- files: {files}",
        f"- privacy: {args.privacy}",
    ]
    if args.decision:
        lines.extend(["", "Decision:", bullet_lines(args.decision)])
    if args.pitfall:
        lines.extend(["", "Pitfall:", bullet_lines(args.pitfall)])
    if args.next:
        lines.extend(["", "Next:", bullet_lines(args.next)])
    return "\n".join(lines) + "\n\n"


def append_memory(args: argparse.Namespace, repo: Path) -> None:
    if args.memory_decision:
        append(
            repo / "ai-memory" / "decisions.md",
            f"## {args.date} - {args.title}\n\n"
            f"Context: {args.goal or 'Not specified.'}\n"
            f"Project: {args.project}\n"
            f"Decision: {'; '.join(args.memory_decision)}\n"
            f"Evidence: remote worklog entry `{args.date} - {args.title}`.\n\n",
        )
    if args.memory_pitfall:
        append(
            repo / "ai-memory" / "pitfalls.md",
            f"## {args.date} - {args.title}\n\n"
            f"Symptom: {'; '.join(args.memory_pitfall)}\n"
            f"Project: {args.project}\n"
            "Cause: Not specified.\n"
            "Fix: See linked worklog entry.\n"
            f"Evidence: remote worklog entry `{args.date} - {args.title}`.\n\n",
        )


def clone_or_init(remote: str, branch: str, target: Path) -> None:
    proc = subprocess.run(
        ["git", "clone", "--branch", branch, remote, str(target)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if proc.returncode == 0:
        return
    if "Remote branch" in proc.stderr or "empty repository" in proc.stderr:
        run(["git", "init", "-b", branch, str(target)])
        run(["git", "remote", "add", "origin", remote], cwd=target)
        return
    raise SystemExit(proc.stderr.strip() or proc.stdout.strip())


def main() -> int:
    today = dt.date.today().isoformat()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--remote", default=os.environ.get("AI_WORKLOG_REMOTE", DEFAULT_REMOTE))
    parser.add_argument("--branch", default="main")
    parser.add_argument("--title", required=True)
    parser.add_argument("--goal", default="")
    parser.add_argument("--changed", action="append", default=[])
    parser.add_argument("--decision", action="append", default=[])
    parser.add_argument("--pitfall", action="append", default=[])
    parser.add_argument("--next", action="append", default=[])
    parser.add_argument("--file", action="append", default=[])
    parser.add_argument("--artifact-commit", default="")
    parser.add_argument("--project", default="", help="Project slug for filtering future memory bootstrap")
    parser.add_argument("--tag", action="append", default=[], help="Optional tag for retrieval")
    parser.add_argument("--privacy", choices=["public", "project"], default="public")
    parser.add_argument("--date", default=today)
    parser.add_argument("--memory-decision", action="append", default=[])
    parser.add_argument("--memory-pitfall", action="append", default=[])
    parser.add_argument("--message", default="")
    parser.add_argument(
        "--skip-scan",
        action="store_true",
        help="Skip pre-push scan. Use only after manual review.",
    )
    args = parser.parse_args()
    if not args.project:
        args.project = "global"
    args.project = slugify(args.project)

    with tempfile.TemporaryDirectory(prefix="ai-worklog-publish-") as tmp:
        repo = Path(tmp) / "repo"
        clone_or_init(args.remote, args.branch, repo)
        ensure_base(repo)
        month = args.date[:7]
        log_path = repo / "ai-log" / f"{month}.md"
        if not log_path.exists():
            log_path.write_text(f"# {month} AI Worklog\n\n", encoding="utf-8")
        append(log_path, build_log_entry(args))
        append_memory(args, repo)
        if not args.skip_scan:
            scan_result = scan_secrets.main_with_args(repo, ["README.md", "ai-log", "ai-memory"])
            if scan_result != 0:
                raise SystemExit("Refusing to publish until scan findings are removed.")

        run(["git", "add", ".gitignore", "README.md", "ai-log", "ai-memory"], cwd=repo)
        if not run(["git", "status", "--short"], cwd=repo):
            print("No worklog changes to publish.")
            return 0
        message = args.message or f"Add AI worklog entry for {args.date}"
        run(["git", "commit", "-m", message], cwd=repo)
        run(["git", "push", "-u", "origin", args.branch], cwd=repo)
        print(f"Published worklog entry to {args.remote}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
