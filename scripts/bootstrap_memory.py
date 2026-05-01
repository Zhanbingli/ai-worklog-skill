#!/usr/bin/env python3
"""Load compact project memory from a remote AI worklog repository."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import tempfile
from pathlib import Path

from ai_worklog.common import default_branch, load_config, run, slugify


DEFAULT_REMOTE = "https://github.com/Zhanbingli/ai-worklog.git"


def infer_project(repo: Path) -> str:
    if not repo.exists():
        return "unknown"
    remote = run(["git", "-C", str(repo), "remote", "get-url", "origin"], check=False)
    if remote:
        remote = remote.removesuffix(".git")
        return slugify(remote.rsplit("/", 1)[-1])
    root = run(["git", "-C", str(repo), "rev-parse", "--show-toplevel"], check=False)
    return slugify(Path(root or repo).name)


def split_sections(text: str) -> list[str]:
    sections: list[str] = []
    current: list[str] = []
    for line in text.splitlines():
        if line.startswith("## ") and current:
            sections.append("\n".join(current).strip())
            current = [line]
        else:
            current.append(line)
    if current:
        block = "\n".join(current).strip()
        if block:
            sections.append(block)
    return sections


def matches_project(block: str, project: str, include_global: bool) -> bool:
    project = project.lower()
    lower = block.lower()
    project_fields = re.findall(r"(?im)^-\s*project:\s*(.+)$|^project:\s*(.+)$", block)
    values = [item for pair in project_fields for item in pair if item]
    if values:
        return any(slugify(value) == project for value in values)
    if not include_global:
        return False
    return "project:" not in lower


def trim_text(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 80].rstrip() + "\n\n[trimmed to fit context budget]"


def sparse_clone(remote: str, branch: str, target: Path, project: str, include_legacy: bool) -> None:
    run(
        [
            "git",
            "clone",
            "--depth",
            "1",
            "--filter=blob:none",
            "--no-checkout",
            "--branch",
            branch,
            remote,
            str(target),
        ]
    )
    paths = [f"ai-index/{project}.json", f"ai-summary/{project}", f"ai-log/{project}", f"ai-memory/{project}"]
    if include_legacy:
        paths.extend(["ai-log/*.md", "ai-memory/*.md"])
    run(["git", "sparse-checkout", "init", "--no-cone"], cwd=target)
    run(["git", "sparse-checkout", "set", *paths], cwd=target)
    run(["git", "checkout", branch], cwd=target)


def read_matching_memory(repo: Path, project: str, include_legacy: bool, max_sections: int) -> dict[str, list[str]]:
    results: dict[str, list[str]] = {}
    for name in ["decisions.md", "pitfalls.md", "prompts.md"]:
        paths = [repo / "ai-memory" / project / name]
        if include_legacy:
            paths.append(repo / "ai-memory" / name)
        matches: list[str] = []
        for path in paths:
            if not path.exists():
                continue
            for section in split_sections(path.read_text(encoding="utf-8")):
                if not section.startswith("## "):
                    continue
                if path.parent.name == project or matches_project(section, project, include_legacy):
                    matches.append(section)
        results[name] = matches[:max_sections]
    return results


def read_matching_logs(repo: Path, project: str, include_legacy: bool, max_entries: int) -> list[str]:
    entries: list[str] = []
    paths = sorted((repo / "ai-log" / project).glob("*.md"), reverse=True)
    if include_legacy:
        paths.extend(sorted((repo / "ai-log").glob("*.md"), reverse=True))
    for path in paths:
        for section in split_sections(path.read_text(encoding="utf-8")):
            if section.startswith("## ") and (
                path.parent.name == project or matches_project(section, project, include_legacy)
            ):
                entries.append(section)
                if len(entries) >= max_entries:
                    return entries
    return entries


def read_summaries(repo: Path, project: str, max_sections: int) -> list[str]:
    summary_root = repo / "ai-summary" / project
    paths = sorted(summary_root.glob("monthly/*.md"), reverse=True)
    paths.extend(sorted(summary_root.glob("weekly/*.md"), reverse=True))
    summaries: list[str] = []
    for path in paths:
        if path.exists():
            summaries.append(f"## {path.relative_to(repo)}\n\n{path.read_text(encoding='utf-8').strip()}")
            if len(summaries) >= max_sections:
                break
    return summaries


def read_index(repo: Path, project: str) -> dict[str, object]:
    path = repo / "ai-index" / f"{project}.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def render_index(data: dict[str, object]) -> list[str]:
    if not data:
        return []
    parts = ["## Compact Project Index", ""]
    latest = data.get("latest_entries", [])
    if isinstance(latest, list) and latest:
        parts.extend(["### Latest Entries", ""])
        for item in latest[:10]:
            if isinstance(item, dict):
                parts.append(
                    f"- {item.get('date', '')}: {item.get('title', '')} "
                    f"({item.get('commit', 'pending')}) - {item.get('summary', '')}"
                )
        parts.append("")
    for key, title in [("decisions", "Recent Decisions"), ("pitfalls", "Recent Pitfalls")]:
        values = data.get(key, [])
        if isinstance(values, list) and values:
            parts.extend([f"### {title}", ""])
            for item in values[:10]:
                if isinstance(item, dict):
                    parts.append(f"- {item.get('date', '')}: {item.get('text', '')}")
            parts.append("")
    return parts


def main() -> int:
    early = argparse.ArgumentParser(add_help=False)
    early.add_argument("--repo", default=".")
    early_args, _ = early.parse_known_args()
    config = load_config(Path(early_args.repo).resolve())
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--remote",
        default=os.environ.get("AI_WORKLOG_REMOTE") or str(config.get("remote") or DEFAULT_REMOTE),
    )
    parser.add_argument("--branch", default="", help="Remote branch. Defaults to remote HEAD, then main.")
    parser.add_argument("--repo", default=".", help="Current project repo used to infer project slug")
    parser.add_argument("--project", default="", help="Project slug. Defaults to current repo name/remote")
    parser.add_argument(
        "--include-legacy",
        action="store_true",
        help="Also read old global ai-log/*.md and ai-memory/*.md files.",
    )
    parser.add_argument("--max-log-entries", type=int, default=5)
    parser.add_argument("--max-memory-sections", type=int, default=5)
    parser.add_argument("--max-summary-sections", type=int, default=2)
    parser.add_argument("--max-chars", type=int, default=12000)
    args = parser.parse_args()

    project = slugify(args.project or str(config.get("project") or "")) if (args.project or config.get("project")) else infer_project(Path(args.repo).resolve())
    branch = args.branch or default_branch(args.remote)
    with tempfile.TemporaryDirectory(prefix="ai-worklog-bootstrap-") as tmp:
        clone = Path(tmp) / "repo"
        sparse_clone(args.remote, branch, clone, project, args.include_legacy)
        index = read_index(clone, project)
        summaries = read_summaries(clone, project, args.max_summary_sections)
        memory = read_matching_memory(clone, project, args.include_legacy, args.max_memory_sections)
        logs = read_matching_logs(clone, project, args.include_legacy, args.max_log_entries)

        parts = [
            "# AI Worklog Project Memory",
            "",
            f"- project: `{project}`",
            f"- source: `{args.remote}`",
            "- scope: project directory only unless --include-legacy is used",
            "",
        ]
        parts.extend(render_index(index))
        if summaries:
            parts.extend(["## Recent Project Summaries", "", "\n\n".join(summaries), ""])
        for name, sections in memory.items():
            if not sections:
                continue
            parts.extend([f"## {name}", "", "\n\n".join(sections), ""])
        if logs:
            parts.extend(["## Recent Matching Worklog Entries", "", "\n\n".join(logs), ""])
        if not any(memory.values()) and not logs:
            parts.extend(["No matching project memory found.", ""])

        print(trim_text("\n".join(parts), args.max_chars))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
