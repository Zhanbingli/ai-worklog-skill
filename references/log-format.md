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
python scripts/append_worklog.py --repo . --title "Task title" --goal "One-sentence goal" --changed "Concrete result"
```

The script creates `ai-log/YYYY-MM.md` when missing, marks the commit as `pending` while the repo is dirty, and fills files from the working tree or the last commit.
