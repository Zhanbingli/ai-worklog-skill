#!/usr/bin/env python3
"""Generate compact weekly or monthly AI worklog summaries."""

from __future__ import annotations

import argparse
import datetime as dt
import re
from pathlib import Path

from ai_worklog.common import frontmatter, iter_markdown_entries, slugify, split_frontmatter_block


def period_bounds(period: str, anchor: dt.date) -> tuple[str, dt.date, dt.date]:
    if period == "weekly":
        start = anchor - dt.timedelta(days=anchor.weekday())
        end = start + dt.timedelta(days=6)
        iso = anchor.isocalendar()
        return f"{iso.year}-W{iso.week:02d}", start, end
    start = dt.date(anchor.year, anchor.month, 1)
    if anchor.month == 12:
        end = dt.date(anchor.year + 1, 1, 1) - dt.timedelta(days=1)
    else:
        end = dt.date(anchor.year, anchor.month + 1, 1) - dt.timedelta(days=1)
    return anchor.strftime("%Y-%m"), start, end


def month_range(start: dt.date, end: dt.date) -> list[str]:
    months: list[str] = []
    current = dt.date(start.year, start.month, 1)
    stop = dt.date(end.year, end.month, 1)
    while current <= stop:
        months.append(current.strftime("%Y-%m"))
        current = dt.date(current.year + 1, 1, 1) if current.month == 12 else dt.date(current.year, current.month + 1, 1)
    return months


def extract_title(body: str, fallback: str) -> str:
    for line in body.splitlines():
        if line.startswith("## "):
            title = line[3:].strip()
            return re.sub(r"^\d{4}-\d{2}-\d{2}\s+-\s+", "", title)
    return fallback


def extract_line(body: str, prefix: str) -> str:
    for line in body.splitlines():
        if line.startswith(prefix):
            return line.split(":", 1)[1].strip()
    return ""


def extract_bullets(body: str, heading: str, limit: int = 4) -> list[str]:
    lines = body.splitlines()
    bullets: list[str] = []
    active = False
    for line in lines:
        stripped = line.strip()
        if stripped == heading:
            active = True
            continue
        if active and stripped.endswith(":") and not stripped.startswith("- "):
            break
        if active and stripped.startswith("- "):
            bullets.append(stripped[2:].strip())
            if len(bullets) >= limit:
                break
    return bullets


def load_entries(repo: Path, project: str, start: dt.date, end: dt.date) -> list[dict[str, object]]:
    results: list[dict[str, object]] = []
    for month in month_range(start, end):
        path = repo / "ai-log" / project / f"{month}.md"
        if not path.exists():
            continue
        for block in iter_markdown_entries(path.read_text(encoding="utf-8")):
            meta, body = split_frontmatter_block(block)
            if str(meta.get("project", "")) != project:
                continue
            date_text = str(meta.get("date", ""))
            try:
                entry_date = dt.date.fromisoformat(date_text)
            except ValueError:
                continue
            if start <= entry_date <= end:
                results.append(
                    {
                        "date": entry_date,
                        "title": extract_title(body, str(meta.get("id", ""))),
                        "goal": extract_line(body, "Goal:"),
                        "changed": extract_bullets(body, "Changed:"),
                        "decisions": extract_bullets(body, "Decision:"),
                        "pitfalls": extract_bullets(body, "Pitfall:"),
                        "files": meta.get("files", []),
                        "commit": str(meta.get("commit", "pending")),
                    }
                )
    return sorted(results, key=lambda item: str(item["date"]))


def bullet(items: list[str], fallback: str = "none") -> str:
    values = [item for item in items if item]
    if not values:
        values = [fallback]
    return "\n".join(f"- {item}" for item in values)


def flatten(values: list[object]) -> list[str]:
    flattened: list[str] = []
    for value in values:
        if isinstance(value, list):
            for item in value:
                text = str(item)
                if text and text not in flattened:
                    flattened.append(text)
        else:
            text = str(value)
            if text and text not in flattened:
                flattened.append(text)
    return flattened


def render_summary(repo: Path, project: str, period: str, anchor: dt.date) -> tuple[str, str]:
    key, start, end = period_bounds(period, anchor)
    entries = load_entries(repo, project, start, end)
    title_period = "Weekly" if period == "weekly" else "Monthly"
    meta = frontmatter(
        {
            "project": project,
            "period": period,
            "key": key,
            "range": f"{start.isoformat()}..{end.isoformat()}",
            "entry_count": str(len(entries)),
        }
    )
    lines = [
        meta,
        "",
        f"# AI {title_period} Summary - {project} - {key}",
        "",
        f"Range: {start.isoformat()}..{end.isoformat()}",
        f"Entries: {len(entries)}",
        "",
        "## Completed Work",
        "",
    ]
    if entries:
        for entry in entries:
            lines.append(f"- {entry['date']}: {entry['title']} ({entry['commit']}) - {entry['goal'] or 'No goal recorded.'}")
    else:
        lines.append("- none")

    changed = flatten([item for entry in entries for item in entry["changed"]])[:20]
    decisions = flatten([item for entry in entries for item in entry["decisions"]])[:20]
    pitfalls = flatten([item for entry in entries for item in entry["pitfalls"]])[:20]
    files = flatten([entry["files"] for entry in entries])[:30]

    lines.extend(["", "## Notable Changes", "", bullet(changed)])
    lines.extend(["", "## Decisions", "", bullet(decisions)])
    lines.extend(["", "## Pitfalls", "", bullet(pitfalls)])
    lines.extend(["", "## Files", "", bullet(files)])
    lines.append("")
    return key, "\n".join(lines)


def write_summary(repo: Path, project: str, period: str, anchor: dt.date) -> Path:
    key, text = render_summary(repo, project, period, anchor)
    path = repo / "ai-summary" / project / period / f"{key}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=".", help="Worklog repository")
    parser.add_argument("--project", required=True, help="Project slug")
    parser.add_argument("--period", choices=["weekly", "monthly"], default="weekly")
    parser.add_argument("--date", default=dt.date.today().isoformat(), help="Anchor date YYYY-MM-DD")
    parser.add_argument("--write", action="store_true", help="Write to ai-summary/<project>/<period>/")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    project = slugify(args.project)
    anchor = dt.date.fromisoformat(args.date)
    if args.write:
        print(write_summary(repo, project, args.period, anchor))
    else:
        _, text = render_summary(repo, project, args.period, anchor)
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
