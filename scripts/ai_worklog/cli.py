"""Unified CLI for the ai-worklog skill.

Dispatches subcommands to the standalone scripts that live alongside this
package so they can still be invoked directly. Each subcommand keeps its
own argparse-based interface — pass `<subcommand> --help` for details.
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

COMMANDS: dict[str, tuple[str, str]] = {
    "init": ("init_project", "Initialize a project for worklogs (.ai-worklog.json, ai-log/, ai-memory/)."),
    "bootstrap": ("bootstrap_memory", "Load compact project memory from the remote worklog at session start."),
    "log": ("append_worklog", "Append a personal changelog entry to ai-log/<project>/YYYY-MM.md."),
    "publish": ("publish_worklog", "Publish a sanitized entry to the remote worklog repository."),
    "draft": ("draft_from_git", "Generate a draft entry from current git status, diff, and commits."),
    "git-context": ("collect_git_context", "Print branch, commit, status, diff stats, and changed files."),
    "weekly": ("weekly_context", "Collect git + worklog context for a weekly review."),
    "summarize": ("summarize_worklog", "Write weekly or monthly rollups under ai-summary/<project>/."),
    "validate": ("validate_worklog", "Validate worklog structure, required frontmatter, and indexes."),
    "scan": ("scan_secrets", "Scan worklog files for obvious secrets and raw transcript markers."),
    "migrate": ("migrate_legacy_logs", "Copy old global-format records into project-scoped directories."),
}

ALIASES = {"summary": "summarize", "context": "git-context"}


def _ensure_scripts_on_path() -> None:
    scripts_dir = Path(__file__).resolve().parent.parent
    path = str(scripts_dir)
    if path not in sys.path:
        sys.path.insert(0, path)


def _print_help() -> None:
    width = max(len(name) for name in COMMANDS)
    lines = ["Usage: ai-worklog <command> [args...]", "", "Commands:"]
    for name, (_, summary) in COMMANDS.items():
        lines.append(f"  {name.ljust(width)}  {summary}")
    lines += [
        "",
        "Run `ai-worklog <command> --help` for command-specific options.",
        "Aliases: " + ", ".join(f"{k}->{v}" for k, v in ALIASES.items()),
    ]
    print("\n".join(lines))


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args or args[0] in {"-h", "--help", "help"}:
        _print_help()
        return 0
    cmd = ALIASES.get(args[0], args[0])
    if cmd not in COMMANDS:
        print(f"ai-worklog: unknown command '{args[0]}'\n", file=sys.stderr)
        _print_help()
        return 2
    module_name, _ = COMMANDS[cmd]
    _ensure_scripts_on_path()
    module = importlib.import_module(module_name)
    saved_argv = sys.argv
    try:
        sys.argv = [f"ai-worklog {cmd}", *args[1:]]
        result = module.main()
    finally:
        sys.argv = saved_argv
    return int(result or 0)


if __name__ == "__main__":
    raise SystemExit(main())
