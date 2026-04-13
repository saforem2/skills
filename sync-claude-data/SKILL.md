---
name: sync-claude-data
description: Use when the user wants to sync, aggregate, or pull Claude Code usage data from remote machines. Triggers on "sync claude data", "pull usage from remote", "aggregate insights", "sync from server", or any request about combining Claude Code stats across machines.
user-invocable: true
allowed-tools:
  - Bash(~/.claude/skills/sync-claude-data/scripts/sync-claude-data.sh *)
  - Bash(rsync *)
  - Read
---

# Sync Claude Data

Pull Claude Code usage data from remote machines via rsync and show aggregated stats.

## Usage

```
/sync-claude-data                          # sync all configured hosts
/sync-claude-data myserver.example.com     # sync a specific host
```

## How It Works

1. Run the sync script:
   ```bash
   ~/.claude/skills/sync-claude-data/scripts/sync-claude-data.sh [HOSTS...]
   ```

2. The script rsyncs `usage-data/`, `stats-cache.json`, `history.jsonl`, `projects/`, and `sessions/` from each remote `~/.claude/` into `~/.claude/aggregated/<hostname>/`.

3. Present the aggregated summary to the user — total messages, sessions, and tool calls per machine plus combined totals.

## Configuration

Edit the `HOSTS` array at the top of `scripts/sync-claude-data.sh` to add your SSH hostnames. Hosts must be reachable via `ssh` (key-based auth recommended).

## Data Layout

```
~/.claude/aggregated/
  myserver-example-com/
    usage-data/
    stats-cache.json
    history.jsonl
    projects/
    sessions/
  another-host/
    ...
```
