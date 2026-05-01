---
name: ai-worklog
description: Create durable AI-assisted work records for software or writing projects. Use when the user asks to log an AI session, maintain an AI changelog, preserve project memory, create build-in-public notes, summarize a task for future Codex/Claude sessions, or turn work into reusable GitHub-backed records without storing unnecessary private prompt transcripts.
---

# AI Worklog

## Overview

Record what changed, why it changed, and what future agents should know. Keep the default output concise and useful for retrieval; preserve raw prompts only when the user explicitly asks for audit-grade logging.

## Record Types

Choose the smallest record that satisfies the user's goal:

- **Personal changelog**: one concise entry per completed task in `ai-log/YYYY-MM.md`.
- **Project memory**: decisions, rejected options, assumptions, and pitfalls in `ai-memory/*.md`.
- **Build-in-public note**: narrative Markdown for readers, usually daily or weekly.
- **Audit trail**: raw prompts, diffs, timestamps, and tool context. Keep private by default.

Do not justify this workflow using broad claims about "literate vs oral" culture. Frame the value in concrete terms: recall, public learning trace, searchable project memory, or debugging.

## Workflow

1. Identify the audience: self, public readers, future agent, or audit/debug.
2. Inspect the current repo state before writing records:
   ```bash
   python skills/ai-worklog/scripts/collect_git_context.py --repo .
   ```
3. Write or update the smallest useful record:
   - Use `ai-log/YYYY-MM.md` for completed task summaries.
   - Use `ai-memory/decisions.md` for durable decisions.
   - Use `ai-memory/pitfalls.md` for failure modes and fixes.
   - Use `ai-memory/prompts.md` only for reusable prompt patterns, not private transcripts.
4. Link records to commits when available. If no commit exists yet, reference changed files and say `commit: pending`.
5. Keep raw conversation and full prompt transcripts out of git unless the user explicitly asks for audit logging. If raw logs are needed, prefer `.ai-raw/` and add it to `.gitignore`.
6. After editing records, show the user what was added and mention any missing commit/test context.

## Writing Rules

- Write for future retrieval, not for performance theater.
- Prefer concrete nouns: files, commits, decisions, failed approaches, follow-up tasks.
- Separate facts from interpretation. Mark uncertain context as `assumption`.
- Keep personal changelog entries short enough to scan in one minute.
- Do not include secrets, credentials, PHI, private user data, or long verbatim prompt transcripts in public logs.
- When creating build-in-public notes, rewrite as narrative and remove private operational detail.

## Default Files

Create files on demand:

```text
ai-log/
  YYYY-MM.md
ai-memory/
  decisions.md
  pitfalls.md
  prompts.md
.ai-raw/        # private, gitignored, only when audit logging is requested
```

For field templates and examples, read `references/log-format.md`.

## Resources

- `scripts/collect_git_context.py`: collect branch, commit, status, diff stats, and changed files.
- `references/log-format.md`: schemas for changelog, memory, public note, and audit records.

## Completion Checklist

- The record says what changed and why.
- The record names commits or changed files.
- Durable project memory is separated from public storytelling.
- Private raw logs are excluded from git unless explicitly requested.
