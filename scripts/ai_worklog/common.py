from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path


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


def entry_id(date: str, project: str, title: str, commit: str = "") -> str:
    base = f"{date}:{project}:{title}:{commit}"
    digest = hashlib.sha1(base.encode("utf-8")).hexdigest()[:10]
    return f"{date}-{project}-{slugify(title)[:48]}-{digest}"


def yaml_scalar(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def yaml_list(values: list[str]) -> str:
    return "[" + ", ".join(yaml_scalar(value) for value in values) + "]"


def frontmatter(fields: dict[str, str | list[str]]) -> str:
    lines = ["---"]
    for key, value in fields.items():
        if isinstance(value, list):
            lines.append(f"{key}: {yaml_list(value)}")
        else:
            lines.append(f"{key}: {yaml_scalar(value)}")
    lines.append("---")
    return "\n".join(lines)


def default_branch(remote: str, fallback: str = "main") -> str:
    output = run(["git", "ls-remote", "--symref", remote, "HEAD"], check=False)
    for line in output.splitlines():
        if line.startswith("ref: refs/heads/") and line.endswith("\tHEAD"):
            return line.split("refs/heads/", 1)[1].split("\t", 1)[0]
    return fallback


def load_config(start: Path | None = None) -> dict[str, object]:
    root = (start or Path.cwd()).resolve()
    candidates = []
    if root.is_file():
        candidates.append(root)
        root = root.parent
    candidates.append(root / ".ai-worklog.json")
    git_root = run(["git", "-C", str(root), "rev-parse", "--show-toplevel"], check=False)
    if git_root:
        candidates.append(Path(git_root) / ".ai-worklog.json")
    candidates.append(Path.cwd() / ".ai-worklog.json")
    for path in candidates:
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data
    return {}


def config_list(config: dict[str, object], key: str) -> list[str]:
    value = config.get(key)
    if isinstance(value, list):
        return [str(item) for item in value]
    if isinstance(value, str) and value:
        return [value]
    return []
