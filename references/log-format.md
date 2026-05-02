# AI Worklog Formats

Use these schemas as defaults. Create only the sections that help future retrieval.

## Privacy Labels

- `public`: safe for GitHub, portfolio, newsletter, or build-in-public.
- `project`: safe for the project repository; avoid publishing without review.
- `private`: keep in `.ai-raw/` or another gitignored location.
- `never`: do not record. Includes secrets, tokens, PHI, private account data, and long verbatim prompt transcripts.

## Personal Changelog

File: `ai-log/<project>/YYYY-MM.md`

```md
---
id: "YYYY-MM-DD-project-short-title-hash"
date: "YYYY-MM-DD"
project: "stable-project-slug"
tags: ["tag", "tag"]
privacy: "public"
commit: "short-sha or pending"
files: ["path", "path"]
---

## YYYY-MM-DD - Short task title

Goal: one sentence.

Changed:
- Concrete result.
- Concrete result.

Artifacts:
- project: stable-project-slug
- tags: tag, tag
- commit: short-sha or pending
- files: path, path
- privacy: public, project, or private

Decision:
- Optional. Why this approach won.

Pitfall:
- Optional. What failed or should be avoided next time.

Next:
- Optional follow-up.
```

## Project Memory

File: `ai-memory/<project>/decisions.md`

```md
## YYYY-MM-DD - Decision title

Context: what forced the decision.
Project: stable-project-slug
Decision: what was chosen.
Rejected: serious alternatives and why they were rejected.
Implication: what future agents should preserve or revisit.
Evidence: commits, files, issues, docs, or user preference.
```

File: `ai-memory/<project>/pitfalls.md`

```md
## YYYY-MM-DD - Pitfall title

Symptom: what went wrong.
Project: stable-project-slug
Cause: known cause or assumption.
Fix: what worked.
Avoid: what future agents should not repeat.
Evidence: commits, files, logs, or commands.
```

File: `ai-memory/<project>/prompts.md`

```md
## Prompt Pattern - Name

Use when: situation.
Prompt:
> concise reusable prompt, with private details removed

Notes: expected output shape and known limitations.
```

## Build-In-Public Note

Use this when the audience is public readers. Do not publish raw tool logs, private prompts, secrets, or messy implementation details.

```md
# Title

Today I tried to ...

What changed:
- Reader-facing result.

What I learned:
- Reflection that is useful beyond this repo.

What I would do differently:
- Concrete improvement.
```

## Audit Record

Keep private by default, preferably under `.ai-raw/` and gitignored.

```md
# YYYY-MM-DDTHH-MM-SS - Audit Record

Task:
Raw prompt summary:
Tool timeline:
Diff links:
Failure or question being audited:
```

## Append Script

Use `scripts/append_worklog.py` for standard personal changelog entries:

```bash
python scripts/append_worklog.py --repo . --title "Task title" --goal "One-sentence goal" --changed "Concrete result" --privacy project
```

The script creates `ai-log/<project>/YYYY-MM.md` when missing, marks the commit as `pending` while the repo is dirty, and fills files from the working tree or the last commit.

## Remote Publishing

Use `scripts/publish_worklog.py` when records should go straight to a GitHub worklog repository without leaving a local worklog checkout. The script has no built-in default remote; pass `--remote`, set `AI_WORKLOG_REMOTE`, or initialize `.ai-worklog.json`. Always pass `--project` unless the record is intentionally global.

Example:

```bash
python scripts/publish_worklog.py --remote "https://github.com/<user>/ai-worklog.git" --project "project-slug" --title "Task title" --goal "One-sentence goal" --changed "Concrete result"
```

The script uses a temporary sparse clone, checks out only `.gitignore`, `README.md`, `ai-log/<project>/`, `ai-memory/<project>/`, and `ai-index/<project>.json`, pushes, and cleans the temporary directory.

Remote publishing runs `scripts/scan_secrets.py` before pushing. It blocks obvious API keys, GitHub tokens, private key blocks, assignment-style secrets such as `token=...`, `.env` references, and raw transcript markers.

Publishing also updates `ai-index/<project>.json`, a compact machine-readable index with latest entries, decisions, and pitfalls. Bootstrap reads this first to reduce token use before falling back to Markdown sections.

Publishing updates weekly and monthly rollups under `ai-summary/<project>/` unless `--no-summary` is passed. Bootstrap reads these summaries before detailed log entries.

## Git Drafting

Use `scripts/draft_from_git.py` to create a draft from current git context:

```bash
python scripts/draft_from_git.py --repo . --title "Task title" --goal "One-sentence goal"
```

Codex should rewrite the `Changed`, `Decision`, and `Pitfall` sections from the git context and user-provided task history before publishing.

## Remote Memory Bootstrap

Use `scripts/bootstrap_memory.py` at the start of a new session to load compact background for only the current project:

```bash
python scripts/bootstrap_memory.py --repo .
```

Project matching primarily uses the project directory: `ai-log/<project>/` and `ai-memory/<project>/`. The `project:` and `Project:` fields remain as redundant metadata and for legacy fallback. If a project uses a different name than the repo directory, pass it explicitly:

```bash
python scripts/bootstrap_memory.py --project "project-slug"
```

Use `--max-log-entries`, `--max-memory-sections`, and `--max-chars` to control token budget. Use `--include-legacy` only when old global-format records are needed.

Bootstrap uses `git clone --depth 1 --filter=blob:none --no-checkout` plus sparse checkout, so it does not fetch other project directories.

## Secret Scan

Use `scripts/scan_secrets.py` before committing or publishing local worklogs:

```bash
python scripts/scan_secrets.py --repo .
```

If it reports findings, remove or rewrite the flagged material. Do not publish with `--skip-scan` unless the user explicitly accepts the risk after reviewing the exact findings.

## Structure Validation

Use `scripts/validate_worklog.py` before committing local records:

```bash
python scripts/validate_worklog.py --repo .
```

It checks project-scoped `ai-log/<project>/YYYY-MM.md` entries for required frontmatter (`id`, `date`, `project`, `tags`, `privacy`, `commit`, `files`), required body sections (`Goal:`, `Changed:`, `Artifacts:`), project/date path consistency, memory retrieval fields, and `ai-index/<project>.json` shape.

## Project Initialization

Use `scripts/init_project.py` once per repository:

```bash
python scripts/init_project.py --repo . --project "project-slug" --remote "https://github.com/<user>/ai-worklog.git" --tag "tag"
```

It creates `ai-log/<project>/`, `ai-memory/<project>/decisions.md`, `ai-memory/<project>/pitfalls.md`, `ai-memory/<project>/prompts.md`, `.ai-raw/`, `.ai-worklog.json`, and a `.gitignore` entry for `.ai-raw/`.

## Project Configuration

`.ai-worklog.json` is intentional project configuration, not cache:

```json
{
  "project": "project-slug",
  "remote": "https://github.com/<user>/ai-worklog.git",
  "default_tags": ["tag"]
}
```

`publish_worklog.py`, `bootstrap_memory.py`, `append_worklog.py`, `draft_from_git.py`, and `weekly_context.py` read this file when command-line arguments do not override it.

## Legacy Migration

Use `scripts/migrate_legacy_logs.py` to copy old global-format records into project directories:

```bash
python scripts/migrate_legacy_logs.py --repo /path/to/ai-worklog --default-project "project-slug"
```

The migration is additive and idempotent: it copies sections into `ai-log/<project>/` and `ai-memory/<project>/` without deleting old files.

## Weekly Summary Context

Use `scripts/weekly_context.py` before asking Codex to write a weekly review:

```bash
python scripts/weekly_context.py --repo . --since 2026-04-24
```

Codex should turn the output into a short private review or a sanitized public note depending on the requested audience.

## Summary Rollups

Use `scripts/summarize_worklog.py` to write compact machine-readable summaries:

```bash
python scripts/summarize_worklog.py --repo . --project "project-slug" --period weekly --write
python scripts/summarize_worklog.py --repo . --project "project-slug" --period monthly --write
```

Summary files live at:

```text
ai-summary/<project>/weekly/YYYY-Www.md
ai-summary/<project>/monthly/YYYY-MM.md
```

These are not polished public essays. They are compact retrieval aids for future agents: completed work, notable changes, decisions, pitfalls, and touched files.
