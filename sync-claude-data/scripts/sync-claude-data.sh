#!/usr/bin/env bash
# Sync Claude Code usage data from remote machines to this Mac.
# Usage: ./sync-claude-data.sh [hostname...]
#        ./sync-claude-data.sh              # syncs all configured hosts
#        ./sync-claude-data.sh myserver     # syncs just myserver
#
# Add your SSH hostnames here:
HOSTS=(
  # "login.example.com"
  # "workstation.internal"
)

AGGREGATE_DIR="$HOME/.claude/aggregated"
REMOTE_CLAUDE_DIR=".claude"

# What to sync — these are the files that matter for usage/insights
SYNC_PATHS=(
  "usage-data/"
  "stats-cache.json"
  "history.jsonl"
  "projects/"
  "sessions/"
)

mkdir -p "$AGGREGATE_DIR"

# Use CLI args if provided, otherwise use configured HOSTS
if [ $# -gt 0 ]; then
  targets=("$@")
else
  targets=("${HOSTS[@]}")
fi

if [ ${#targets[@]} -eq 0 ]; then
  echo "No hosts configured. Edit HOSTS in this script or pass hostnames as arguments."
  echo "  Example: $0 login.example.com workstation.internal"
  exit 1
fi

for host in "${targets[@]}"; do
  slug=$(echo "$host" | tr '.:@' '-')
  dest="$AGGREGATE_DIR/$slug"
  mkdir -p "$dest"

  echo "=== Syncing from $host -> $dest ==="

  for path in "${SYNC_PATHS[@]}"; do
    echo "  rsync $path ..."
    rsync -az --timeout=30 \
      "$host:~/$REMOTE_CLAUDE_DIR/$path" \
      "$dest/$path" 2>/dev/null || echo "  [skip] $path not found on $host"
  done

  echo "  Done."
  echo ""
done

# Show summary
echo "=== Aggregate summary ==="
for dir in "$AGGREGATE_DIR"/*/; do
  host=$(basename "$dir")
  stats="$dir/stats-cache.json"
  if [ -f "$stats" ]; then
    sessions=$(python3 -c "
import json
d = json.load(open('$stats'))
total_msgs = sum(x.get('messageCount', 0) for x in d.get('dailyActivity', []))
total_sess = sum(x.get('sessionCount', 0) for x in d.get('dailyActivity', []))
total_tools = sum(x.get('toolCallCount', 0) for x in d.get('dailyActivity', []))
print(f'{total_msgs} messages, {total_sess} sessions, {total_tools} tool calls')
" 2>/dev/null)
    echo "  $host: $sessions"
  else
    echo "  $host: no stats-cache.json"
  fi
done

# Local stats too
local_stats="$HOME/.claude/stats-cache.json"
if [ -f "$local_stats" ]; then
  local_summary=$(python3 -c "
import json
d = json.load(open('$local_stats'))
total_msgs = sum(x.get('messageCount', 0) for x in d.get('dailyActivity', []))
total_sess = sum(x.get('sessionCount', 0) for x in d.get('dailyActivity', []))
total_tools = sum(x.get('toolCallCount', 0) for x in d.get('dailyActivity', []))
print(f'{total_msgs} messages, {total_sess} sessions, {total_tools} tool calls')
" 2>/dev/null)
  echo "  local: $local_summary"
fi
