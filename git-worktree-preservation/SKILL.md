---
name: git-worktree-preservation
description: Use when refreshing, archiving, or salvaging git worktrees.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [git, worktrees, preservation, integration]
    related_skills: [upstream-sync-and-integration, github-pr-workflow]
---

# Git Worktree Preservation

## When to Use

Use whenever a task asks to refresh a primary checkout, archive obsolete worktrees, salvage a useful edit from a dirty checkout, or clean up validation trees after a campaign.

## Procedure

1. **Inventory before moving refs.** Fetch the target remote branch, then record for every relevant checkout:
   - path, branch/detached state, HEAD, upstream, ahead/behind counts;
   - tracked status separately from untracked artifacts;
   - processes whose current working directory is inside the tree;
   - running jobs or builds that name the tree.

   A tracked edit, active process CWD, or overlapping untracked path is a preservation boundary. Do not switch, reset, pull, clean, or force-remove that checkout.

2. **Refresh only clean checkouts.** For a clean detached checkout whose HEAD is an ancestor of the desired remote head, use `git checkout --detach <immutable-sha>`. For a clean branch use a fast-forward-only update. Re-read HEAD and status afterward. If the primary checkout is dirty, advance a clean isolated worktree instead and report the exact preservation reason; do not make the primary look current by discarding work.

3. **Promote useful stranded edits instead of leaving them local.** When a valid fix exists only in a dirty or obsolete checkout:
   - compare it with the current product branch;
   - recreate the minimal edit in a clean managed worktree under the configured home-based worktree root;
   - add a focused regression test;
   - run the repository's exact hooks and tests;
   - land it through the normal PR/CI path.

   Leave the original dirty checkout untouched until its owner reconciles it. Duplicating a verified edit is safer than overwriting unrelated work.

4. **Archive campaign worktrees as provenance.** Before retiring a tree, require terminal scheduler state and no active CWD. Copy or move job logs, status, HEAD, and relevant artifact paths into a dated archive; write a machine-readable manifest with sizes and hashes. Remove only clean inactive worktrees. If untracked logs block `git worktree remove`, move the whole tree intact into the archive and prune only the stale Git registration. Never force-delete a modified tree.

5. **Handle hook fallout on historically noncompliant files.** A changed-file CI hook may apply current formatter, spelling, or lint rules to the entire touched file. Run the exact CI hook set, inspect the full generated diff, accept deterministic normalization and minimal legacy cleanup only when scoped and reviewed, and discard broad type-checker rewrites outside the intended surface. Rerun until the second pass is clean.

6. **Verify final state.** Confirm remote ancestry/merge state, archive manifests, remaining preserved exceptions, and a clean current isolated worktree. Report preserved trees explicitly with the reason they were not refreshed or removed.

## Always-on Rules

- Never use `reset --hard`, `clean`, forced checkout, or force-removal to refresh a shared or dirty checkout.
- Place manually created worktrees under the configured durable home-based worktree root, never a temporary directory.
- Treat untracked files as unknown ownership until inspected; “untracked” does not mean disposable.
- Do not call an archived directory a working Git worktree after pruning its registration; preserve its recorded SHA in the archive manifest.
- A useful local edit should either be promoted to the product branch with tests or explicitly rejected; do not leave canonical fixes stranded in stale checkouts.
