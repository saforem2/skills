# Shared Agent Skills

[`saforem2/skills`](https://github.com/saforem2/skills) is the shared source for these skills, not a Claude-only installation directory. Each top-level skill directory contains a `SKILL.md` and any supporting assets. Keep one source checkout and expose its flat skill directories through each agent's native discovery mechanism.

## Setup

```bash
git clone https://github.com/saforem2/skills.git ~/.agents/skills
```

If that directory already contains local skills or another checkout, **do not replace it**. Clone elsewhere, inventory both roots, and resolve ownership and name conflicts first. Existing local edits are not disposable. Update the source checkout with `git -C ~/.agents/skills pull --ff-only` only after reviewing its working tree.

### Agent discovery

| Agent | Native discovery / integration |
| --- | --- |
| Codex | Flat directories under `~/.agents/skills/`. The example checkout is already in this shared discovery root. |
| Oh My Pi (OMP) | Native shared discovery from flat directories under `~/.agents/skills/`; no registry publication required. `~/.omp/agent/skills/` is another supported root. |
| OpenCode 1 | Supports both `~/.config/opencode/skills/` and the shared `~/.agents/skills/` root. |
| OpenCode 2 (`opencode2`) | Also reads the shared root. Its explicit extra-source config uses a `skills` array, unlike v1's `skills.paths`. |
| Claude Code | Per-skill directory symlinks under `~/.claude/skills/`, pointing to this checkout. Do not replace an existing skills root with a whole-directory symlink. |
| Hermes | Add the source checkout to `skills.external_dirs` using `hermes config set`, as below. |

Native discovery is not proof that every skill's tools or commands work in every agent. Review prerequisites and adapt agent-specific instructions before use.

### Inventory and non-destructive links

The installer uses only Python's standard library. `inventory ROOTS...` reports discovered skills and asset hashes; its output includes local paths and should not be published without review.

```bash
python3 scripts/skill_library.py inventory ~/.agents/skills ~/.claude/skills

# Preview only (the default):
python3 scripts/skill_library.py install --source ~/.agents/skills --destination ~/.claude/skills

# After reviewing the plan:
python3 scripts/skill_library.py install --source ~/.agents/skills --destination ~/.claude/skills --apply
```

Use a verified native discovery root as `--destination` for another agent. The installer creates **per-skill symlinks**, not copies. Existing links to the same source are left alone; conflicting directories, files, or broken links are never overwritten. A dry run reports conflicts without changing anything; `--apply` refuses the entire known-conflicting batch. Duplicate or unsafe skill names are rejected. Keep the source checkout available for as long as links depend on it.

### Hermes external directory

Configure the active Hermes profile through the CLI only; do not hand-edit its configuration file:

```bash
hermes config set skills.external_dirs '["~/.agents/skills"]'
```

This sets the whole list: preserve any existing external directories by including them in the value. Start a fresh session and inspect the discovered skills. **Precedence matters:** trusted project skills, profile-local skills, and `skills.create_dir` can shadow external skills with the same name; external-directory mounting does not force this checkout to win. Resolve duplicates deliberately rather than deleting local skills or claiming that mounting alone verifies convergence.

## Skills

| Skill | Description |
| --- | --- |
| [`summarize-events`](summarize-events/) | Summarize Outlook calendar events and GitHub commit activity for date ranges. |
| [`alcf_run`](alcf_run/) | Submit PBS jobs and run commands on ALCF compute nodes. |
| [`torchtitan-ezpz-smoke-test`](torchtitan-ezpz-smoke-test/) | Run torchtitan-ezpz smoke tests on ALCF compute nodes and write benchmark reports. |
| [`sync-claude-data`](sync-claude-data/) | Sync Claude Code usage data from remote machines for aggregated insights. |
| [`update-custom-skills`](update-custom-skills/) | Update the resolved canonical checkout safely; preserve dirty trees and refresh consumer links deliberately. |
| [`falsification-first-debugging`](falsification-first-debugging/) | Test competing explanations before fixing an uncertain failure. |
| [`minimal-dependency-defect-probes`](minimal-dependency-defect-probes/) | Isolate a defect with a small, dependency-light reproduction. |
| [`git-worktree-preservation`](git-worktree-preservation/) | Preserve local work when refreshing or archiving worktrees. |
| [`validation-check-authoring`](validation-check-authoring/) | Demonstrate that validation checks fail under negative controls. |
| [`generated-file-merge-conflicts`](generated-file-merge-conflicts/) | Address recurring merge conflicts in generated files. |
| [`scientific-figure-typography`](scientific-figure-typography/) | Keep publication figure typography consistent. |

## Configuration and validation

Some original skills still require local configuration, which must not be committed:

- `summarize-events/.env`: Outlook calendar ICS/HTML URLs.
- `sync-claude-data/scripts/sync-claude-data.sh`: configure the `HOSTS` array for your own SSH hosts.

Run the same dependency-free checks used by CI:

```bash
python3 -m unittest discover -s tests -v
git diff --check
```

These checks cover installer behavior and patch whitespace, not end-to-end execution in every agent or on remote compute systems. See [consolidation scope and provenance](docs/consolidation.md) for what is included and what remains deferred. The repository [MIT license](LICENSE) and individual skill attribution remain applicable.
