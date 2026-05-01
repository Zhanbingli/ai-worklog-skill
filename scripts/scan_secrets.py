#!/usr/bin/env python3
"""Scan AI worklog files for obvious secrets or private raw material."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


DEFAULT_INCLUDE = ["README.md", "ai-log", "ai-memory"]
SKIP_DIRS = {".git", ".ai-raw", "__pycache__", ".venv", "node_modules"}
TEXT_SUFFIXES = {".md", ".txt", ".yml", ".yaml", ".json", ".toml", ".gitignore", ""}
PATTERNS = [
    ("openai_api_key", re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b")),
    ("anthropic_api_key", re.compile(r"\bsk-ant-[A-Za-z0-9_-]{20,}\b")),
    ("github_token", re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b")),
    ("slack_token", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{20,}\b")),
    ("google_api_key", re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b")),
    ("azure_key", re.compile(r"(?i)\bazure[_-]?(api[_-]?)?key\s*[:=]\s*['\"]?[A-Za-z0-9+/=]{20,}")),
    ("jwt", re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b")),
    ("private_key", re.compile(r"-----BEGIN (?:RSA |DSA |EC |OPENSSH |PGP )?PRIVATE KEY-----")),
    ("aws_access_key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("aws_secret_key", re.compile(r"(?i)\baws(.{0,20})?(secret|private).{0,20}\s*[:=]\s*['\"]?[A-Za-z0-9/+=]{30,}")),
    ("assignment_secret", re.compile(r"(?i)\b(password|passwd|pwd|token|secret|api[_-]?key|client[_-]?secret)\s*[:=]\s*['\"]?[^'\"\s]{8,}")),
    ("env_file_reference", re.compile(r"(^|/)\.env(\.|$|/)")),
    ("email_address", re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")),
    ("raw_transcript_marker", re.compile(r"(?i)^\s*(raw transcript|full transcript|verbatim prompt|完整 prompt|原始对话)\s*:")),
]


def iter_files(root: Path, includes: list[str]) -> list[Path]:
    files: list[Path] = []
    for item in includes:
        path = root / item
        if not path.exists():
            continue
        if path.is_file():
            files.append(path)
            continue
        for child in path.rglob("*"):
            if any(part in SKIP_DIRS for part in child.parts):
                continue
            if child.is_file():
                files.append(child)
    return files


def is_text_file(path: Path) -> bool:
    return path.suffix in TEXT_SUFFIXES or path.name == ".gitignore"


def scan_file(path: Path, root: Path) -> list[str]:
    if not is_text_file(path):
        return []
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return []
    findings: list[str] = []
    rel = path.relative_to(root)
    for line_no, line in enumerate(text.splitlines(), start=1):
        for name, pattern in PATTERNS:
            if pattern.search(line):
                findings.append(f"{rel}:{line_no}: {name}")
    return findings


def run_scan(root: Path, includes: list[str]) -> int:
    findings: list[str] = []
    for path in iter_files(root, includes):
        findings.extend(scan_file(path, root))

    if findings:
        print("Potential private or secret material found:", file=sys.stderr)
        for finding in findings:
            print(f"- {finding}", file=sys.stderr)
        return 1
    print("No obvious secret or raw transcript markers found.")
    return 0


def main_with_args(root: Path, includes: list[str]) -> int:
    return run_scan(root.resolve(), includes or DEFAULT_INCLUDE)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=".", help="Repository or directory to scan")
    parser.add_argument(
        "--include",
        action="append",
        default=[],
        help="Path to scan. Defaults to README.md, ai-log, and ai-memory.",
    )
    args = parser.parse_args()

    return run_scan(Path(args.repo).resolve(), args.include or DEFAULT_INCLUDE)


if __name__ == "__main__":
    raise SystemExit(main())
