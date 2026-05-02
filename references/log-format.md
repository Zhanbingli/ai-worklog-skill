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

## CLI Reference

All operations are exposed through `<SKILL_DIR>/scripts/ai-worklog <command>`. The legacy standalone scripts under `scripts/<name>.py` still work and accept the same arguments — the CLI just dispatches to them. Pass `--help` to any subcommand for its full option list.

### `init` — one-time project setup

```bash
ai-worklog init --repo . --project "project-slug" --remote "https://github.com/<user>/ai-worklog.git" --tag "tag"
```

Creates `ai-log/<project>/`, `ai-memory/<project>/{decisions,pitfalls,prompts}.md`, `.ai-raw/`, `.ai-worklog.json`, and a `.gitignore` entry for `.ai-raw/`.

`.ai-worklog.json` is intentional project configuration, not cache:

```json
{
  "project": "project-slug",
  "remote": "https://github.com/<user>/ai-worklog.git",
  "default_tags": ["tag"]
}
```

`log`, `publish`, `bootstrap`, `draft`, and `weekly` read this file when CLI flags do not override it.

### `log` — append a personal changelog entry

```bash
ai-worklog log --repo . --title "Task title" --goal "One-sentence goal" --changed "Concrete result" --privacy project
```

Creates `ai-log/<project>/YYYY-MM.md` when missing, marks the commit as `pending` while the repo is dirty, and fills `files` from the working tree or the last commit.

### `publish` — push a sanitized entry to the remote worklog

```bash
ai-worklog publish --remote "https://github.com/<user>/ai-worklog.git" --project "project-slug" --title "Task title" --goal "One-sentence goal" --changed "Concrete result"
```

No built-in default remote — pass `--remote`, set `AI_WORKLOG_REMOTE`, or rely on `.ai-worklog.json`. The command:

1. Sparse-clones the remote into a temp directory (only `.gitignore`, `README.md`, `ai-log/<project>/`, `ai-memory/<project>/`, `ai-summary/<project>/`, `ai-index/<project>.json`).
2. Writes the sanitized entry, updates `ai-index/<project>.json`, refreshes weekly/monthly rollups under `ai-summary/<project>/` (skip with `--no-summary`).
3. Runs `validate` and `scan`. Refuses to push on failure.
4. Pushes and removes the temp clone.

`scan` blocks obvious API keys, GitHub tokens, private key blocks, `token=...`-style assignments, `.env` references, and raw transcript markers. Do not bypass with `--skip-scan` unless the user explicitly accepts the risk after reviewing the exact findings.

### `bootstrap` — load compact project memory at session start

```bash
ai-worklog bootstrap --repo .
ai-worklog bootstrap --project "project-slug"   # if repo dir != project slug
```

Uses `git clone --depth 1 --filter=blob:none --no-checkout` + sparse checkout so it fetches only `ai-log/<project>/`, `ai-memory/<project>/`, `ai-summary/<project>/`, and `ai-index/<project>.json`. Reads the index first, then summaries, then detailed entries. Use `--max-log-entries`, `--max-memory-sections`, and `--max-chars` to control token budget. Use `--include-legacy` only when old global-format records are needed.

### `draft` — entry draft from git

```bash
ai-worklog draft --repo . --title "Task title" --goal "One-sentence goal"
```

The agent should rewrite `Changed`, `Decision`, and `Pitfall` from the git context and user-provided history before passing the result to `publish`.

### `validate` — structure check

```bash
ai-worklog validate --repo .
```

Checks `ai-log/<project>/YYYY-MM.md` entries for required frontmatter (`id`, `date`, `project`, `tags`, `privacy`, `commit`, `files`), required body sections (`Goal:`, `Changed:`, `Artifacts:`), project/date path consistency, memory retrieval fields, and `ai-index/<project>.json` shape. Run before committing local records; `publish` runs it automatically.

### `scan` — secret scan

```bash
ai-worklog scan --repo .
```

If it reports findings, remove or rewrite the flagged material before committing or publishing.

### `weekly` — context for weekly reviews

```bash
ai-worklog weekly --repo . --since 2026-04-24
```

The agent should turn the output into a short private review or a sanitized public note depending on the requested audience.

### `summarize` — weekly/monthly rollups

```bash
ai-worklog summarize --repo . --project "project-slug" --period weekly --write
ai-worklog summarize --repo . --project "project-slug" --period monthly --write
```

Output lives at:

```text
ai-summary/<project>/weekly/YYYY-Www.md
ai-summary/<project>/monthly/YYYY-MM.md
```

These are not polished essays. They are compact retrieval aids for future agents: completed work, notable changes, decisions, pitfalls, and touched files.

### `migrate` — adopt project layout from old global logs

```bash
ai-worklog migrate --repo /path/to/ai-worklog --default-project "project-slug"
```

Additive and idempotent: copies sections into `ai-log/<project>/` and `ai-memory/<project>/` without deleting old files.
