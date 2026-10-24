---
name: update-custom-skills
description: Use when the user wants to update, refresh, or pull the latest custom skills. Triggers on "update skills", "pull skills", "refresh skills", "sync skills", or "get latest skills".
user-invocable: true
---

# Update Custom Skills

Update the canonical `saforem2/skills` checkout, not a harness's consumer links.
This procedure works across agents with shell access.

## Steps

1. Resolve this skill directory's real path, following symlinks. Find its Git
   repository root with `git -C <resolved-skill-directory> rev-parse --show-toplevel`.
   Do not assume the checkout is `~/.claude/skills`, `~/.codex/skills`, or even
   `~/.agents/skills`: linked worktrees and alternate installations are valid.
2. Inspect `git -C <root> remote -v`, `status --short --branch`, and
   `branch --show-current`. Confirm the intended repository and branch. Stop on
   local modifications, untracked content, detached HEAD, or an unexpected
   remote; report what needs reconciliation. Never reset, clean, stash, switch
   branches, or bulk-stage someone else's skills to make an update pass.
3. Record HEAD, then run `git -C <root> pull --ff-only`. A divergent history is
   a reconciliation task, not permission to force an update.
4. Read back HEAD and status. Summarize actual changes and preserved exceptions.
   Existing directory links follow the updated source; do not create copies.
   New skill directories may need fresh consumer links: use this repository's
   `scripts/skill_library.py install --source <root> --destination <native-root>`
   dry run first, then apply only a reviewed conflict-free plan.
5. Verify discovery in each affected agent. Already-running sessions may cache
   their catalogs; distinguish source updates from live-session refreshes.
