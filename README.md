# Claude Code Skills

Custom skills for [Claude Code](https://docs.anthropic.com/en/docs/claude-code). Clone into `~/.claude/skills/` to use.

## Setup

```bash
git clone https://github.com/saforem2/skills.git ~/.claude/skills
```

To update: `/update-custom-skills` or `git -C ~/.claude/skills pull`

## Skills

| Skill | Description |
|-------|-------------|
| [`summarize-events`](summarize-events/) | Summarize Outlook calendar events and GitHub commit activity for any date range. Supports `--last`/`--next` day\|week\|month\|year and custom ranges. |
| [`alcf_run`](alcf_run/) | Submit PBS jobs and run commands on ALCF compute nodes (Sunspot, Aurora, Polaris). |
| [`torchtitan-ezpz-smoke-test`](torchtitan-ezpz-smoke-test/) | Run smoke tests for torchtitan-ezpz experiments on ALCF compute nodes and write benchmark reports. |
| [`update-custom-skills`](update-custom-skills/) | Pull the latest skills from this repo. |

## Configuration

Some skills require local configuration (not tracked by git):

- `summarize-events/.env` — Outlook calendar ICS/HTML URLs
