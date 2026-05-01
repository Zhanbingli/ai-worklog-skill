# AI Worklog Skill

Reusable Codex skill for recording AI-assisted work as concise changelogs, project memory, public learning notes, or private audit records.

## Install

Clone this repository and copy it into your Codex skills directory:

```bash
git clone https://github.com/Zhanbingli/ai-worklog-skill.git
mkdir -p ~/.codex/skills
cp -R ai-worklog-skill ~/.codex/skills/ai-worklog
```

## Use

Ask Codex:

```text
Use $ai-worklog to summarize this session into a concise changelog and project memory update.
```

The skill defaults to short, searchable records and keeps raw prompt transcripts private unless audit logging is explicitly requested.

## Files

- `SKILL.md`: workflow and usage rules.
- `scripts/collect_git_context.py`: collect git status, diff stats, branch, and changed files.
- `references/log-format.md`: templates for changelog, project memory, public notes, and audit records.
