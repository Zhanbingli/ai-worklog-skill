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
python ~/.codex/skills/ai-worklog/scripts/publish_worklog.py --title "Task title" --goal "One-sentence goal" --changed "Concrete result"
```

For another repository:

```bash
python ~/.codex/skills/ai-worklog/scripts/publish_worklog.py --remote "https://github.com/<user>/ai-worklog.git" --title "Task title" --goal "One-sentence goal" --changed "Concrete result"
```

`publish_worklog.py` uses a temporary clone, pushes the sanitized Markdown records, and removes the temporary directory when it exits. Do not use it for raw transcripts, secrets, private data, or audit logs.

### Project-local records

Initialize a project once:

```bash
python ~/.codex/skills/ai-worklog/scripts/init_project.py --repo .
```

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

Privacy defaults:

- `public`: safe for GitHub or build-in-public.
- `project`: safe in the project repo, not automatically public.
- `private`: keep gitignored under `.ai-raw/`.
- `never`: do not record secrets, tokens, PHI, private account data, or long prompt transcripts.

## Files

- `SKILL.md`: workflow and usage rules.
- `scripts/init_project.py`: initialize a project for worklogs and private raw logs.
- `scripts/collect_git_context.py`: collect git status, diff stats, branch, and changed files.
- `scripts/append_worklog.py`: create and append `ai-log/YYYY-MM.md` entries.
- `scripts/publish_worklog.py`: publish a sanitized entry to a remote worklog repo using only a temporary clone.
- `scripts/weekly_context.py`: collect context for weekly reviews.
- `references/log-format.md`: templates for changelog, project memory, public notes, and audit records.
