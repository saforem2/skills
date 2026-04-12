---
name: summarize-events
description: Use when the user wants to see, summarize, list, or review calendar events, git activity, or produce a weekly report for any time period. Triggers on phrases like "what's on my calendar", "summarize last week", "upcoming meetings", "my schedule", "weekly report", "what did I work on", or any request involving calendar/meeting/event/commit summaries.
user-invocable: true
allowed-tools:
  - Bash(uv run *)
  - Bash(gh api *)
  - Read
---

# Summarize Events & Activity

Fetch and summarize Outlook calendar events and GitHub commit activity for any date range.

## Usage

```
/summarize-events                          # last week (default)
/summarize-events --last day|week|month|year
/summarize-events --next day|week|month|year
/summarize-events --start 2026-03-01 --end 2026-03-31
```

## How It Works

Run both scripts in parallel, then combine results.

### Step 1: Fetch calendar events

```bash
uv run ~/.claude/skills/summarize-events/scripts/fetch_ics_events.py [ARGS] 2>/tmp/ics_stderr.txt
```

Pass through user arguments (`--last`, `--next`, `--start`/`--end`). The script reads the ICS URL from `~/.claude/skills/summarize-events/.env`.

**Playwright fallback:** If stderr contains `---NO_EVENTS_FOUND---`, the ICS feed didn't cover the requested range. Fall back to browser automation:
1. Read `html_calendar_url` from JSON output and navigate to it
2. Wait 5s, then use navigation buttons to reach the target date range
3. Click each event button, read the dialog via `document.querySelector('[role="dialog"]').innerText`, close, repeat
4. Filter out "Focus time" and "Canceled" events

### Step 2: Fetch git activity

```bash
uv run ~/.claude/skills/summarize-events/scripts/fetch_git_activity.py [ARGS]
```

Same date arguments as step 1. Uses the `gh` CLI to search commits. Add `--exclude Notes` to skip noisy repos.

### Step 3: Present combined results

Show the user:
1. **Calendar** — markdown table (Date, Time, Event, Location) + text summary grouped by day
2. **Git Activity** — markdown table (Date, Repo, Commit, Message) + summary grouped by repo, with repo stats

### Step 4: Weekly report (if requested)

If the user asks to categorize or produce a weekly report, read `references/weekly-report-template.md` and categorize events + commits into the template sections.

## Configuration

`~/.claude/skills/summarize-events/.env`:
```
OUTLOOK_CALENDAR_ICS_URL=https://outlook.office365.com/owa/calendar/...calendar.ics
OUTLOOK_CALENDAR_HTML_URL=https://outlook.office365.com/calendar/published/...calendar.html
```
