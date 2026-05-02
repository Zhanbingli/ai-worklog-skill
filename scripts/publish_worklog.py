#!/usr/bin/env python3
"""Publish a sanitized AI worklog entry to a remote GitHub repository.

The script clones the remote into a temporary directory, writes only the
worklog/memory files, pushes the commit, and removes the temporary directory.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import scan_secrets
import summarize_worklog
import validate_worklog
from ai_worklog.common import config_list, default_branch, entry_id, frontmatter, load_config, run, slugify


def bullet_lines(items: list[str], fallback: str = "Not specified.") -> str:
    values = [item.strip() for item in items if item.strip()]
    if not values:
        values = [fallback]
    return "\n".join(f"- {item}" for item in values)


def append(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(text)
        if not text.endswith("\n"):
            handle.write("\n")


def ensure_base(repo: Path, project: str) -> None:
    (repo / "ai-log").mkdir(parents=True, exist_ok=True)
    (repo / "ai-memory").mkdir(parents=True, exist_ok=True)
    (repo / "ai-summary").mkdir(parents=True, exist_ok=True)
    (repo / "ai-log" / project).mkdir(parents=True, exist_ok=True)
    (repo / "ai-memory" / project).mkdir(parents=True, exist_ok=True)
    (repo / "ai-summary" / project / "weekly").mkdir(parents=True, exist_ok=True)
    (repo / "ai-summary" / project / "monthly").mkdir(parents=True, exist_ok=True)
    (repo / "ai-index").mkdir(parents=True, exist_ok=True)
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
        ("decisions.md", f"# AI Project Decisions - {project}\n\n"),
        ("pitfalls.md", f"# AI Project Pitfalls - {project}\n\n"),
        ("prompts.md", f"# Reusable AI Prompt Patterns - {project}\n\n"),
    ]:
        path = repo / "ai-memory" / project / name
        if not path.exists():
            path.write_text(title, encoding="utf-8")


def ensure_git_identity(repo: Path) -> None:
    name = run(["git", "config", "--get", "user.name"], cwd=repo, check=False)
    email = run(["git", "config", "--get", "user.email"], cwd=repo, check=False)
    if not name:
        run(["git", "config", "user.name", "AI Worklog Bot"], cwd=repo)
    if not email:
        run(["git", "config", "user.email", "ai-worklog@example.invalid"], cwd=repo)


def build_log_entry(args: argparse.Namespace) -> str:
    files = ", ".join(args.file) if args.file else "none"
    commit = args.artifact_commit or "pending"
    meta = frontmatter(
        {
            "id": entry_id(args.date, args.project, args.title, commit),
            "date": args.date,
            "project": args.project,
            "tags": args.tag,
            "privacy": args.privacy,
            "commit": commit,
            "files": args.file,
        }
    )
    lines = [
        meta,
        "",
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
        f"- commit: {commit}",
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


def update_index(args: argparse.Namespace, repo: Path) -> None:
    path = repo / "ai-index" / f"{args.project}.json"
    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
    else:
        data = {"project": args.project, "latest_entries": [], "decisions": [], "pitfalls": []}

    commit = args.artifact_commit or "pending"
    item = {
        "id": entry_id(args.date, args.project, args.title, commit),
        "date": args.date,
        "title": args.title,
        "project": args.project,
        "tags": args.tag,
        "privacy": args.privacy,
        "commit": commit,
        "files": args.file,
        "summary": args.goal,
    }
    latest = [item]
    for existing in data.get("latest_entries", []):
        if isinstance(existing, dict) and existing.get("id") != item["id"]:
            latest.append(existing)
    data["latest_entries"] = latest[:20]

    for key, values in [("decisions", args.memory_decision), ("pitfalls", args.memory_pitfall)]:
        existing = data.get(key, [])
        additions = [{"date": args.date, "title": args.title, "text": value} for value in values]
        data[key] = (additions + existing)[:50] if isinstance(existing, list) else additions

    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def append_memory(args: argparse.Namespace, repo: Path) -> None:
    if args.memory_decision:
        append(
            repo / "ai-memory" / args.project / "decisions.md",
            f"## {args.date} - {args.title}\n\n"
            f"Context: {args.goal or 'Not specified.'}\n"
            f"Project: {args.project}\n"
            f"Decision: {'; '.join(args.memory_decision)}\n"
            f"Evidence: remote worklog entry `{args.date} - {args.title}`.\n\n",
        )
    if args.memory_pitfall:
        append(
            repo / "ai-memory" / args.project / "pitfalls.md",
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


def sparse_clone_or_init(remote: str, branch: str, target: Path, project: str) -> None:
    proc = subprocess.run(
        [
            "git",
            "clone",
            "--filter=blob:none",
            "--no-checkout",
            "--branch",
            branch,
            remote,
            str(target),
        ],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if proc.returncode == 0:
        run(["git", "sparse-checkout", "init", "--no-cone"], cwd=target)
        run(
            [
                "git",
                "sparse-checkout",
                "set",
                "README.md",
                ".gitignore",
                f"ai-log/{project}",
                f"ai-memory/{project}",
                f"ai-summary/{project}",
                f"ai-index/{project}.json",
            ],
            cwd=target,
        )
        run(["git", "checkout", branch], cwd=target)
        return
    if "Remote branch" in proc.stderr or "empty repository" in proc.stderr:
        run(["git", "init", "-b", branch, str(target)])
        run(["git", "remote", "add", "origin", remote], cwd=target)
        return
    raise SystemExit(proc.stderr.strip() or proc.stdout.strip())


def main() -> int:
    today = dt.date.today().isoformat()
    config = load_config(Path.cwd())
    configured_remote = os.environ.get("AI_WORKLOG_REMOTE") or str(config.get("remote") or "")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--remote",
        default=configured_remote,
        help="Git remote for the worklog repository. Defaults to AI_WORKLOG_REMOTE or .ai-worklog.json.",
    )
    parser.add_argument("--branch", default="", help="Remote branch. Defaults to remote HEAD, then main.")
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
    parser.add_argument(
        "--no-summary",
        action="store_true",
        help="Do not update weekly and monthly ai-summary files after publishing.",
    )
    args = parser.parse_args()
    if not args.remote:
        raise SystemExit(
            "Missing worklog remote. Pass --remote, set AI_WORKLOG_REMOTE, "
            "or run init_project.py with --remote to create .ai-worklog.json."
        )
    if not args.project:
        args.project = str(config.get("project") or "global")
    args.project = slugify(args.project)
    if not args.tag:
        args.tag = config_list(config, "default_tags")
    args.branch = args.branch or default_branch(args.remote)

    with tempfile.TemporaryDirectory(prefix="ai-worklog-publish-") as tmp:
        repo = Path(tmp) / "repo"
        sparse_clone_or_init(args.remote, args.branch, repo, args.project)
        ensure_git_identity(repo)
        ensure_base(repo, args.project)
        month = args.date[:7]
        log_path = repo / "ai-log" / args.project / f"{month}.md"
        if not log_path.exists():
            log_path.write_text(f"# {month} AI Worklog - {args.project}\n\n", encoding="utf-8")
        append(log_path, build_log_entry(args))
        append_memory(args, repo)
        update_index(args, repo)
        if not args.no_summary:
            anchor = dt.date.fromisoformat(args.date)
            summarize_worklog.write_summary(repo, args.project, "weekly", anchor)
            summarize_worklog.write_summary(repo, args.project, "monthly", anchor)
        validation_errors = validate_worklog.validate_logs(repo) + validate_worklog.validate_indexes(repo)
        if validation_errors:
            raise SystemExit("Refusing to publish invalid worklog:\n" + "\n".join(validation_errors))
        if not args.skip_scan:
            scan_result = scan_secrets.main_with_args(repo, ["README.md", "ai-log", "ai-memory", "ai-summary", "ai-index"])
            if scan_result != 0:
                raise SystemExit("Refusing to publish until scan findings are removed.")

        run(
            [
                "git",
                "add",
                ".gitignore",
                "README.md",
                f"ai-log/{args.project}",
                f"ai-memory/{args.project}",
                f"ai-summary/{args.project}",
                f"ai-index/{args.project}.json",
            ],
            cwd=repo,
        )
        if not run(["git", "status", "--short"], cwd=repo):
            print("No worklog changes to publish.")
            return 0
        message = args.message or f"Add AI worklog entry for {args.date}"
        run(["git", "commit", "-m", message], cwd=repo)
        push = subprocess.run(
            ["git", "push", "-u", "origin", args.branch],
            cwd=str(repo),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if push.returncode != 0 and "fetch first" in push.stderr.lower():
            raise SystemExit("Push rejected because the remote moved. Re-run the command to publish against a fresh clone.")
        if push.returncode != 0:
            raise SystemExit(push.stderr.strip() or push.stdout.strip())
        print(f"Published worklog entry to {args.remote}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
