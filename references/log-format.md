# AI Worklog Formats

Use these schemas as defaults. Create only the sections that help future retrieval.

## Privacy Labels

- `public`: safe for GitHub, portfolio, newsletter, or build-in-public.
- `project`: safe for the project repository; avoid publishing without review.
- `private`: keep in `.ai-raw/` or another gitignored location.
- `never`: do not record. Includes secrets, tokens, PHI, private account data, and long verbatim prompt transcripts.

## Personal Changelog

File: `ai-log/YYYY-MM.md`

```md
## YYYY-MM-DD - Short task title

Goal: one sentence.

Changed:
- Concrete result.
- Concrete result.

Artifacts:
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

File: `ai-memory/decisions.md`

```md
## YYYY-MM-DD - Decision title

Context: what forced the decision.
Decision: what was chosen.
Rejected: serious alternatives and why they were rejected.
Implication: what future agents should preserve or revisit.
Evidence: commits, files, issues, docs, or user preference.
```

File: `ai-memory/pitfalls.md`

```md
## YYYY-MM-DD - Pitfall title

Symptom: what went wrong.
Cause: known cause or assumption.
Fix: what worked.
Avoid: what future agents should not repeat.
Evidence: commits, files, logs, or commands.
```

File: `ai-memory/prompts.md`

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

The script creates `ai-log/YYYY-MM.md` when missing, marks the commit as `pending` while the repo is dirty, and fills files from the working tree or the last commit.

## Remote Publishing

Use `scripts/publish_worklog.py` when records should go straight to a GitHub worklog repository without leaving a local worklog checkout.

Default remote for this installation:

```text
https://github.com/Zhanbingli/ai-worklog.git
```

Example:

```bash
python scripts/publish_worklog.py --title "Task title" --goal "One-sentence goal" --changed "Concrete result"
```

For other users, create a GitHub repository first and pass it explicitly:

```bash
python scripts/publish_worklog.py --remote "https://github.com/<user>/ai-worklog.git" --title "Task title" --goal "One-sentence goal" --changed "Concrete result"
```

The script uses a temporary clone, commits only `.gitignore`, `README.md`, `ai-log/`, and `ai-memory/`, pushes, and cleans the temporary directory.

## Project Initialization

Use `scripts/init_project.py` once per repository:

```bash
python scripts/init_project.py --repo .
```

It creates `ai-log/`, `ai-memory/decisions.md`, `ai-memory/pitfalls.md`, `ai-memory/prompts.md`, `.ai-raw/`, and a `.gitignore` entry for `.ai-raw/`.

## Weekly Summary Context

Use `scripts/weekly_context.py` before asking Codex to write a weekly review:

```bash
python scripts/weekly_context.py --repo . --since 2026-04-24
```

Codex should turn the output into a short private review or a sanitized public note depending on the requested audience.
