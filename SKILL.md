---
name: ai-worklog
description: Create durable AI-assisted work records for software or writing projects. Use when the user asks to log an AI session, maintain an AI changelog, preserve project memory, create build-in-public notes, summarize a task for future Codex/Claude sessions, or turn work into reusable GitHub-backed records without storing unnecessary private prompt transcripts.
---

# AI Worklog

Record what changed, why it changed, and what future agents should know. Default output is concise and retrieval-friendly. Raw prompt transcripts are kept out of git unless the user explicitly asks for audit logging.

## Invocation

All operations go through one CLI. `<SKILL_DIR>` is wherever this skill is installed (e.g. `~/.claude/skills/ai-worklog` or `~/.codex/skills/ai-worklog`).

```bash
<SKILL_DIR>/scripts/ai-worklog <command> [args...]
```

Run with no arguments for the command list, or `<command> --help` for options. Subcommands: `init`, `bootstrap`, `log`, `publish`, `draft`, `git-context`, `weekly`, `summarize`, `validate`, `scan`, `migrate`.

## Workflow

1. **First time in a repo** — initialize once. Creates `.ai-worklog.json`, `ai-log/<project>/`, `ai-memory/<project>/`, and a gitignored `.ai-raw/`:
   ```bash
   ai-worklog init --repo . --project PROJECT_SLUG --remote https://github.com/<user>/ai-worklog.git
   ```
2. **Start of session** — bootstrap compact project memory from the remote worklog (sparse clone, no local checkout retained):
   ```bash
   ai-worklog bootstrap --repo .
   ```
3. **After a task** — append a local changelog entry, or publish straight to the remote worklog:
   ```bash
   ai-worklog log --title "..." --goal "..." --changed "..." --privacy project
   ai-worklog publish --title "..." --goal "..." --changed "..."
   ```
4. **Before committing or publishing** — validate structure and scan for secrets. Publishing runs both automatically and refuses on failure:
   ```bash
   ai-worklog validate --repo .
   ai-worklog scan --repo .
   ```

## Record types

Pick the smallest record that satisfies the goal:

- **Personal changelog** — `ai-log/<project>/YYYY-MM.md`, one short entry per task.
- **Project memory** — `ai-memory/<project>/{decisions,pitfalls,prompts}.md` for durable knowledge.
- **Build-in-public note** — narrative Markdown for public readers; sanitize first.
- **Audit trail** — raw prompts and tool timeline. Keep under `.ai-raw/` (gitignored) unless explicitly published.

Always include a stable `project` slug and useful `tags`. Link to commits when available; otherwise reference changed files and mark `commit: pending`.

## Privacy labels

Apply one before writing:

- `public` — safe for GitHub, portfolio, build-in-public.
- `project` — safe inside the project repo, not for public storytelling.
- `private` — keep under `.ai-raw/`, gitignored.
- `never` — secrets, tokens, PHI, private account data, or long verbatim prompt transcripts. Do not record.

Do not write `never` material into any log. Do not publish `private` material. When creating public notes, rewrite as narrative and remove operational detail.

## Writing rules

- Write for future retrieval, not performance theater. Concrete nouns: files, commits, decisions, failed approaches, follow-ups.
- Separate facts from interpretation. Mark uncertain context as `assumption`.
- Personal changelog entries should scan in under a minute.
- After editing records, show the user what was added and call out any missing commit/test context.

## Reference

Read `references/log-format.md` for record schemas, frontmatter fields, and per-subcommand usage.
