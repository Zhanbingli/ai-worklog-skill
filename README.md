# AI Worklog Skill

Reusable Codex skill for recording AI-assisted work as concise changelogs, project memory, public learning notes, or private audit records.

## Install

Clone directly into your Codex skills directory:

```bash
mkdir -p ~/.codex/skills
git clone https://github.com/Zhanbingli/ai-worklog-skill.git ~/.codex/skills/ai-worklog
```

Update later with:

```bash
cd ~/.codex/skills/ai-worklog
git pull
```

## Use

### Remote worklog repository

This install defaults remote publishing to:

```text
https://github.com/Zhanbingli/ai-worklog.git
```

To use the skill yourself, create a GitHub repository such as:

```text
https://github.com/<user>/ai-worklog.git
```

Then pass it with `--remote` or set:

```bash
export AI_WORKLOG_REMOTE="https://github.com/<user>/ai-worklog.git"
```

Publish a public-safe entry without keeping a local worklog checkout:

```bash
python ~/.codex/skills/ai-worklog/scripts/publish_worklog.py --project "project-slug" --title "Task title" --goal "One-sentence goal" --changed "Concrete result"
```

For another repository:

```bash
python ~/.codex/skills/ai-worklog/scripts/publish_worklog.py --remote "https://github.com/<user>/ai-worklog.git" --project "project-slug" --title "Task title" --goal "One-sentence goal" --changed "Concrete result"
```

`publish_worklog.py` uses a temporary clone, pushes the sanitized Markdown records, and removes the temporary directory when it exits. Do not use it for raw transcripts, secrets, private data, or audit logs.

Draft an entry from a project before publishing:

```bash
python ~/.codex/skills/ai-worklog/scripts/draft_from_git.py --repo .
```

Scan a local worklog before committing or publishing:

```bash
python ~/.codex/skills/ai-worklog/scripts/scan_secrets.py --repo .
```

Remote publishing runs this scan by default and refuses to push obvious secrets or raw transcript markers.

Validate local worklog structure:

```bash
python ~/.codex/skills/ai-worklog/scripts/validate_worklog.py --repo .
```

Load only current-project memory at the start of a new session:

```bash
python ~/.codex/skills/ai-worklog/scripts/bootstrap_memory.py --repo .
```

Records are stored under `ai-log/<project>/` and `ai-memory/<project>/`, so publish with stable project slugs and tags. Bootstrap uses sparse checkout to fetch only those project paths. Use `--max-chars`, `--max-log-entries`, and `--max-memory-sections` to keep startup context small.

Publishing also maintains `ai-index/<project>.json`, a compact machine-readable summary that bootstrap reads first to reduce token use. It also maintains `ai-summary/<project>/weekly/` and `ai-summary/<project>/monthly/` so future agents can read rollups before detailed entries.

For project-level startup behavior, add this to that project's `AGENTS.md`:

```md
At the start of substantial work, use $ai-worklog and run:

python ~/.codex/skills/ai-worklog/scripts/bootstrap_memory.py --repo .

Use only the returned project-scoped context. Do not persist the remote worklog clone locally.
```

### Project-local records

Initialize a project once:

```bash
python ~/.codex/skills/ai-worklog/scripts/init_project.py --repo . --project "project-slug" --remote "https://github.com/<user>/ai-worklog.git"
```

This writes `.ai-worklog.json` so later commands can infer the project, remote, and default tags.

After an AI-assisted task, ask Codex:

```text
Use $ai-worklog to summarize this session into a concise changelog and project memory update.
```

The skill defaults to short, searchable records and keeps raw prompt transcripts private unless audit logging is explicitly requested.

To append a standard changelog entry:

```bash
python ~/.codex/skills/ai-worklog/scripts/append_worklog.py --repo . --title "Task title" --goal "One-sentence goal" --changed "Concrete result" --privacy project
```

For a weekly review:

```bash
python ~/.codex/skills/ai-worklog/scripts/weekly_context.py --repo . --since 2026-04-24
```

Then ask Codex:

```text
Use $ai-worklog to turn this weekly context into a private weekly review and a sanitized build-in-public draft.
```

Generate a compact weekly or monthly rollup from project-scoped logs:

```bash
python ~/.codex/skills/ai-worklog/scripts/summarize_worklog.py --repo . --project "project-slug" --period weekly --write
```

Privacy defaults:

- `public`: safe for GitHub or build-in-public.
- `project`: safe in the project repo, not automatically public.
- `private`: keep gitignored under `.ai-raw/`.
- `never`: do not record secrets, tokens, PHI, private account data, or long prompt transcripts.

Migrate old global files into project directories:

```bash
python ~/.codex/skills/ai-worklog/scripts/migrate_legacy_logs.py --repo /path/to/ai-worklog --default-project "project-slug"
```

## Files

- `SKILL.md`: workflow and usage rules.
- `scripts/init_project.py`: initialize a project for worklogs and private raw logs.
- `scripts/collect_git_context.py`: collect git status, diff stats, branch, and changed files.
- `scripts/bootstrap_memory.py`: load compact current-project memory from the remote worklog repo without keeping a local clone.
- `scripts/append_worklog.py`: create and append `ai-log/<project>/YYYY-MM.md` entries.
- `scripts/draft_from_git.py`: generate a draft worklog entry from git status, commits, diff stats, and changed files.
- `scripts/publish_worklog.py`: publish a sanitized entry to a remote worklog repo using only a temporary clone.
- `scripts/scan_secrets.py`: scan worklog files for obvious secrets, tokens, private key markers, and raw transcript markers.
- `scripts/validate_worklog.py`: validate project-scoped worklog structure and machine-readable indexes.
- `scripts/summarize_worklog.py`: generate compact weekly or monthly summaries for future agent bootstrap.
- `scripts/weekly_context.py`: collect context for weekly reviews.
- `scripts/migrate_legacy_logs.py`: copy old `ai-log/YYYY-MM.md` and `ai-memory/*.md` sections into project directories.
- `ai-summary/<project>/`: generated weekly and monthly rollups.
- `ai-index/<project>.json`: generated in worklog repositories by `publish_worklog.py` for compact retrieval.
- `references/log-format.md`: templates for changelog, project memory, public notes, and audit records.
