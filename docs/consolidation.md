# Consolidation scope and provenance

## Shared source, staged rollout

The existing public [`saforem2/skills`](https://github.com/saforem2/skills) repository is the publication source. Its original flat skill directories remain in place. Consolidation adds reusable procedures and non-destructive integration tooling; it is not a bulk import of every installed agent skill or a declaration of complete cross-agent compatibility.

Stages are deliberately separate:

1. Inventory candidate libraries and preserve local edits, existing links, and ownership.
2. Import the selected MIT skills below with their frontmatter attribution and supporting assets.
3. Publish shared-source setup instructions and a dry-run-first per-skill link installer.
4. Configure each intended agent's native discovery mechanism, then verify actual discovery and execution in that agent separately.
5. Review deferred repository-specific skills for licensing, attribution, and adapter requirements before proposing another import.

The first stages do not establish that all agent verification is complete. Neither a symlink nor an inventory entry demonstrates that an agent can execute a skill's workflow.

## Imported local MIT skills

These six procedures originated in the local Hermes skill library and were selected for reuse beyond their original project context. The table records the source skill identities and the attribution retained in their frontmatter; it does not assign new authorship.

| Imported directory | Source frontmatter author | Source license |
| --- | --- | --- |
| [`falsification-first-debugging`](../falsification-first-debugging/) | Hermes | MIT |
| [`minimal-dependency-defect-probes`](../minimal-dependency-defect-probes/) | Hermes Agent | MIT |
| [`git-worktree-preservation`](../git-worktree-preservation/) | Hermes Agent | MIT |
| [`validation-check-authoring`](../validation-check-authoring/) | Hermes Agent | MIT |
| [`generated-file-merge-conflicts`](../generated-file-merge-conflicts/) | Hermes Curator | MIT |
| [`scientific-figure-typography`](../scientific-figure-typography/) | Hermes Curator | MIT |

The repository's [MIT license](../LICENSE) credits Sam Foreman. Preserve applicable license notices and existing frontmatter attribution when editing or redistributing these skills. This provenance record intentionally excludes personal machine paths, private inventories, credentials, and operational host details.

## Dependencies are not republished

Independently maintained upstream skill libraries and their skills remain separate dependencies. They are not vendored, relicensed, or republished by this consolidation. A `related_skills` reference may name a skill outside this repository: that is a relationship, not evidence that the dependency is bundled or installed. Obtain missing upstream dependencies from their own sources under their own licenses.

Existing repository skills may also require external tools, agent-specific commands, authenticated services, schedulers, or local configuration. Sharing their source does not supply those dependencies. Review each skill before execution and keep configuration and secrets outside published artifacts.

## Deferred TorchTitan skills

The six candidate TorchTitan project skills remain unchanged in their source project and are not imported in this stage. Before any transfer, review their BSD licensing and preserve the required attribution and notices. Separate general procedures from TorchTitan-specific paths, launch commands, tool assumptions, and environment requirements; provide and verify adapters where needed.

This deferral concerns those six candidate project skills, not the pre-existing `torchtitan-ezpz-smoke-test` skill already in this repository. No license conversion or portability claim is implied for either group.

## Installation and verification boundaries

`scripts/skill_library.py` inventories roots and plans per-skill symlinks. Installation defaults to a dry run, treats existing incompatible targets as conflicts, and refuses a known-conflicting batch when `--apply` is requested. It does not merge directories, replace local edits, rewrite agent configuration, or install upstream libraries.

Hermes integration uses `hermes config set skills.external_dirs ...` only. Preserve the active profile's existing external-directory list when setting it. Trusted project, profile-local, and creation-directory skills can take precedence over external skills; verify the selected source rather than relying on matching names.

The GitHub Actions workflow runs standard-library unit tests and `git diff --check`. These checks are not a substitute for runtime discovery checks in Codex, OMP, both OpenCode discovery routes, Claude Code, and Hermes, nor for workflow-specific execution tests. Record that evidence independently before claiming full convergence.
