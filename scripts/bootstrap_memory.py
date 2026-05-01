#!/usr/bin/env python3
"""Load compact project memory from a remote AI worklog repository."""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import tempfile
from pathlib import Path


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


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9._/-]+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-")
    return value or "unknown"


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
    paths = [f"ai-log/{project}", f"ai-memory/{project}"]
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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--remote", default=os.environ.get("AI_WORKLOG_REMOTE", DEFAULT_REMOTE))
    parser.add_argument("--branch", default="main")
    parser.add_argument("--repo", default=".", help="Current project repo used to infer project slug")
    parser.add_argument("--project", default="", help="Project slug. Defaults to current repo name/remote")
    parser.add_argument(
        "--include-legacy",
        action="store_true",
        help="Also read old global ai-log/*.md and ai-memory/*.md files.",
    )
    parser.add_argument("--max-log-entries", type=int, default=5)
    parser.add_argument("--max-memory-sections", type=int, default=5)
    parser.add_argument("--max-chars", type=int, default=12000)
    args = parser.parse_args()

    project = slugify(args.project) if args.project else infer_project(Path(args.repo).resolve())
    with tempfile.TemporaryDirectory(prefix="ai-worklog-bootstrap-") as tmp:
        clone = Path(tmp) / "repo"
        sparse_clone(args.remote, args.branch, clone, project, args.include_legacy)
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
