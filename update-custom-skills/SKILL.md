---
name: update-custom-skills
description: Use when the user wants to update, refresh, or pull the latest custom skills. Triggers on "update skills", "pull skills", "refresh skills", "sync skills", or "get latest skills".
user-invocable: true
allowed-tools:
  - Bash(git -C ~/.claude/skills pull)
---

# Update Custom Skills

Pull the latest skills from the remote repository.

## Steps

1. Run:
   ```bash
   git -C ~/.claude/skills pull
   ```
2. Report what changed (new skills, updated files, already up to date).
