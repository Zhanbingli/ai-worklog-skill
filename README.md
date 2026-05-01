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

Ask Codex:

```text
Use $ai-worklog to summarize this session into a concise changelog and project memory update.
```

The skill defaults to short, searchable records and keeps raw prompt transcripts private unless audit logging is explicitly requested.

To append a standard changelog entry:

```bash
python ~/.codex/skills/ai-worklog/scripts/append_worklog.py --repo . --title "Task title" --goal "One-sentence goal" --changed "Concrete result"
```

Privacy defaults:

- `public`: safe for GitHub or build-in-public.
- `project`: safe in the project repo, not automatically public.
- `private`: keep gitignored under `.ai-raw/`.
- `never`: do not record secrets, tokens, PHI, private account data, or long prompt transcripts.

## Files

- `SKILL.md`: workflow and usage rules.
- `scripts/collect_git_context.py`: collect git status, diff stats, branch, and changed files.
- `scripts/append_worklog.py`: create and append `ai-log/YYYY-MM.md` entries.
- `references/log-format.md`: templates for changelog, project memory, public notes, and audit records.
