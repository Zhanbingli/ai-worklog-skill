# AI Worklog Skill

Reusable skill for recording AI-assisted work as concise changelogs, project memory, public learning notes, or private audit records. Works under both Codex (`~/.codex/skills/`) and Claude Code (`~/.claude/skills/`).

## Install

Pick your install target:

```bash
# Codex
git clone https://github.com/Zhanbingli/ai-worklog-skill.git ~/.codex/skills/ai-worklog

# Claude Code
git clone https://github.com/Zhanbingli/ai-worklog-skill.git ~/.claude/skills/ai-worklog
```

Update later with `git pull` from inside that directory.

For convenience, expose the CLI on your PATH:

```bash
ln -s "$HOME/.claude/skills/ai-worklog/scripts/ai-worklog" /usr/local/bin/ai-worklog
# or for Codex:
ln -s "$HOME/.codex/skills/ai-worklog/scripts/ai-worklog" /usr/local/bin/ai-worklog
```

The rest of this README assumes `ai-worklog` is on your PATH. If not, prefix every command with `<SKILL_DIR>/scripts/`.

## CLI

One front door, eleven subcommands:

```bash
ai-worklog                  # show available commands
ai-worklog <command> --help # per-command options
```

| Command | What it does |
|---|---|
| `init` | One-time project setup (`.ai-worklog.json`, `ai-log/`, `ai-memory/`, `.ai-raw/`) |
| `bootstrap` | Sparse-clone the remote worklog and print compact project memory |
| `log` | Append an entry to `ai-log/<project>/YYYY-MM.md` |
| `publish` | Sanitize and push an entry to the remote worklog repo (temp clone, auto-cleaned) |
| `draft` | Generate an entry draft from current git status, diff, and commits |
| `git-context` | Print branch, commit, status, diff stats, changed files |
| `weekly` | Collect git + worklog context for a weekly review |
| `summarize` | Write weekly or monthly rollups under `ai-summary/<project>/` |
| `validate` | Check structure, frontmatter, and indexes |
| `scan` | Scan worklog files for obvious secrets and raw transcript markers |
| `migrate` | Copy old global-format records into project-scoped directories |

The standalone scripts under `scripts/*.py` still work directly if you prefer them, but the CLI is the documented surface.

## Quick start

```bash
# 1. Create your remote worklog repo at https://github.com/<user>/ai-worklog
export AI_WORKLOG_REMOTE="https://github.com/<user>/ai-worklog.git"

# 2. Initialize the project
ai-worklog init --repo . --project "my-project" --remote "$AI_WORKLOG_REMOTE"

# 3. After an AI-assisted task, publish a sanitized entry
ai-worklog publish \
  --title "Task title" \
  --goal "One-sentence goal" \
  --changed "Concrete result"

# 4. Next session, bootstrap project memory
ai-worklog bootstrap --repo .
```

`publish` clones the remote into a temporary directory, writes only sanitized records, pushes, and removes the clone. It runs `validate` and `scan` first and refuses to push on failure. Never use it for raw transcripts, secrets, private data, or audit logs.

## Project layout

After `init` and at least one entry:

```text
ai-log/<project>/YYYY-MM.md           # personal changelog entries
ai-memory/<project>/decisions.md      # durable decisions
ai-memory/<project>/pitfalls.md       # failure modes and fixes
ai-memory/<project>/prompts.md        # reusable prompt patterns
ai-summary/<project>/weekly/          # generated rollups
ai-summary/<project>/monthly/
ai-index/<project>.json               # compact machine-readable index
.ai-raw/                              # private, gitignored
.ai-worklog.json                      # project config (project, remote, default tags)
```

`bootstrap` reads `ai-index/<project>.json` first, then `ai-summary/<project>/`, then detailed log entries, in that order. Use `--max-chars`, `--max-log-entries`, and `--max-memory-sections` to keep startup context small.

## Privacy labels

- `public` — safe for GitHub, portfolio, newsletter, build-in-public.
- `project` — safe inside the project repo; review before publishing.
- `private` — keep gitignored under `.ai-raw/`.
- `never` — secrets, tokens, PHI, private account data, long verbatim prompt transcripts. Do not record.

`publish` blocks obvious secrets (API keys, GitHub tokens, private-key markers, `.env` references, raw transcript markers) via the secret scan. Do not bypass with `--skip-scan` unless you have manually reviewed the findings.

## Project hookup

Add this to your project's `AGENTS.md` or `CLAUDE.md` so each new session bootstraps automatically:

```md
At the start of substantial work, run:

  ai-worklog bootstrap --repo .

Use only the returned project-scoped context. Do not persist the remote worklog clone locally.
```

## Files

- `SKILL.md` — agent-facing workflow.
- `scripts/ai-worklog` — unified CLI entry point.
- `scripts/ai_worklog/` — shared library (`common.py`, `cli.py`).
- `scripts/<command>.py` — implementation per subcommand.
- `references/log-format.md` — record schemas, frontmatter fields, full per-command reference.
