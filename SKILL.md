---
name: ai-worklog
description: Create durable AI-assisted work records for software or writing projects. Use when the user asks to log an AI session, maintain an AI changelog, preserve project memory, create build-in-public notes, summarize a task for future Codex/Claude sessions, or turn work into reusable GitHub-backed records without storing unnecessary private prompt transcripts.
---

# AI Worklog

## Overview

Record what changed, why it changed, and what future agents should know. Keep the default output concise and useful for retrieval; preserve raw prompts only when the user explicitly asks for audit-grade logging.

Default remote record repository for this installation: `https://github.com/Zhanbingli/ai-worklog.git`. For other users, ask them to create their own GitHub repository and pass it with `--remote` or set `AI_WORKLOG_REMOTE`.

Published entries include YAML frontmatter and update `ai-index/<project>.json` so future sessions can bootstrap compact project memory before reading longer Markdown sections.

## Record Types

Choose the smallest record that satisfies the user's goal:

- **Personal changelog**: one concise entry per completed task in `ai-log/<project>/YYYY-MM.md`.
- **Project memory**: decisions, rejected options, assumptions, and pitfalls in `ai-memory/<project>/*.md`.
- **Build-in-public note**: narrative Markdown for readers, usually daily or weekly.
- **Audit trail**: raw prompts, diffs, timestamps, and tool context. Keep private by default.

Do not justify this workflow using broad claims about "literate vs oral" culture. Frame the value in concrete terms: recall, public learning trace, searchable project memory, or debugging.

## Workflow

1. At the start of a new session, load only relevant remote memory for the current project:
   ```bash
   python ~/.codex/skills/ai-worklog/scripts/bootstrap_memory.py --repo .
   ```
   Use `--project PROJECT_SLUG` when the current directory name is not the right project key. Use `--include-legacy` only when the user wants old global-format records.
2. If the project has no worklog structure, initialize it:
   ```bash
   python ~/.codex/skills/ai-worklog/scripts/init_project.py --repo .
   ```
3. Identify the audience: self, public readers, future agent, or audit/debug.
4. Inspect the current repo state before writing records:
   ```bash
   python ~/.codex/skills/ai-worklog/scripts/collect_git_context.py --repo .
   ```
   For a fuller draft from git context, use:
   ```bash
   python ~/.codex/skills/ai-worklog/scripts/draft_from_git.py --repo .
   ```
5. Write or update the smallest useful record:
   - Use `ai-log/<project>/YYYY-MM.md` for completed task summaries.
   - Use `ai-memory/<project>/decisions.md` for durable decisions.
   - Use `ai-memory/<project>/pitfalls.md` for failure modes and fixes.
   - Use `ai-memory/<project>/prompts.md` only for reusable prompt patterns, not private transcripts.
6. Always include `project` and useful `tags` when writing or publishing records. This is the retrieval key that prevents future sessions from reading unrelated logs.
7. Link records to commits when available. If no commit exists yet, reference changed files and say `commit: pending`.
8. Keep raw conversation and full prompt transcripts out of git unless the user explicitly asks for audit logging. If raw logs are needed, prefer `.ai-raw/` and add it to `.gitignore`.
9. After editing records, show the user what was added and mention any missing commit/test context.

For this user's remote-only worklog, publish directly to the default GitHub repository and do not keep a local worklog checkout:

```bash
python ~/.codex/skills/ai-worklog/scripts/publish_worklog.py --project "project-slug" --title "Short task title" --goal "One-sentence goal" --changed "Concrete result"
```

This script clones the worklog repository into a temporary directory, writes sanitized records, pushes the commit, and removes the temporary directory. Never use it for raw transcripts, secrets, private data, or audit logs.

Remote publishing runs `scan_secrets.py` before pushing. If it finds obvious tokens, private-key markers, `.env` references, or raw transcript markers, remove them instead of bypassing the scan.

For another user, ask them to create a repository like `https://github.com/<user>/ai-worklog.git`, then run:

```bash
python ~/.codex/skills/ai-worklog/scripts/publish_worklog.py --remote "https://github.com/<user>/ai-worklog.git" --title "Short task title" --goal "One-sentence goal" --changed "Concrete result"
```

For a standard personal changelog entry, use the append script instead of hand-editing:

```bash
python ~/.codex/skills/ai-worklog/scripts/append_worklog.py --repo . --title "Short task title" --goal "One-sentence goal" --changed "Concrete result"
```

For a weekly review context, use:

```bash
python ~/.codex/skills/ai-worklog/scripts/weekly_context.py --repo . --since YYYY-MM-DD
```

## Writing Rules

- Write for future retrieval, not for performance theater.
- Prefer concrete nouns: files, commits, decisions, failed approaches, follow-up tasks.
- Separate facts from interpretation. Mark uncertain context as `assumption`.
- Keep personal changelog entries short enough to scan in one minute.
- Apply privacy labels before writing:
  - `public`: safe for GitHub, portfolio, or build-in-public.
  - `project`: safe inside the project repo but not for public storytelling.
  - `private`: keep under `.ai-raw/` and gitignored.
  - `never`: secrets, tokens, PHI, private account data, or long verbatim prompt transcripts.
- Do not write `never` material into any log. Do not publish `private` material.
- When creating build-in-public notes, rewrite as narrative and remove private operational detail.

## Default Files

Create files on demand:

```text
ai-log/
  project-slug/
    YYYY-MM.md
ai-memory/
  project-slug/
    decisions.md
    pitfalls.md
    prompts.md
ai-index/
  project-slug.json
.ai-raw/        # private, gitignored, only when audit logging is requested
```

For field templates and examples, read `references/log-format.md`.

## Resources

- `scripts/collect_git_context.py`: collect branch, commit, status, diff stats, and changed files.
- `scripts/bootstrap_memory.py`: temporarily clone the remote worklog, filter entries by project, and print compact startup context.
- `scripts/init_project.py`: create project-scoped `ai-log/`, `ai-memory/`, starter memory files, and `.ai-raw/` ignore rules.
- `scripts/append_worklog.py`: append a standard entry to `ai-log/<project>/YYYY-MM.md`.
- `scripts/draft_from_git.py`: generate a draft entry from git context for Codex to rewrite.
- `scripts/publish_worklog.py`: publish a sanitized entry to a remote worklog repository through a temporary clone that is cleaned automatically.
- `scripts/scan_secrets.py`: scan records for obvious secrets and raw transcript markers before publication.
- `scripts/weekly_context.py`: gather git commits, worktree status, and worklog entries for weekly summaries.
- `references/log-format.md`: schemas for changelog, memory, public note, and audit records.

## Completion Checklist

- The record says what changed and why.
- The record names commits or changed files.
- Durable project memory is separated from public storytelling.
- Private raw logs are excluded from git unless explicitly requested.
