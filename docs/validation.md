# Validation evidence

This records discovery checks for the local consolidation rollout. It does not
claim that every skill's workflow was executed, or that all installed content
was cleared for public redistribution.

## Repository checks

- Seven standard-library unit tests pass: inventory hashes and dotfile
  exclusion, symlink/cycle traversal, idempotent installation, whole-batch
  conflict refusal, broken-link preservation, duplicate names, unsafe names.
- `git diff --check` passes.
- Imported Markdown asset links resolve; screened imports contain no detected
  personal absolute home paths or known private host addresses.
- `provenance.json` retains original asset hashes and declared attribution.

## Local agent discovery

The shared, Hermes, and Claude roots each expose 218 distinct frontmatter
names through existing directories and non-destructive links. Native catalogs
also include built-in/plugin/project entries, so their totals need not match.

| Agent | Actual verification | Result |
| --- | --- | --- |
| Hermes | Native `skills_list` tool | 218 skills |
| OMP | `omp skill list <checkout> --json` | 218 skills, no warnings |
| Codex | Stdio app-server `initialize`, then `skills/list` with `forceReload` | 276 entries, no errors in the checked project |
| OpenCode 1 | `opencode debug skill` | 225 entries |
| OpenCode 2 | GET `/api/skill` for the checked location | 220 entries |
| Claude Code | SDK stream-json `initialize` control request, no user/model turn | 289 commands, including the imported probe skill |

All six native interfaces included `falsification-first-debugging`. Codex and
Claude validation used initialization/control requests only, not model
inference. Disabling Claude's user setting sources or using bare mode did not
advertise the same user-skill catalog; the successful check used normal user
settings with strict MCP configuration and session persistence disabled.

For OpenCode 2, inspect its live OpenAPI schema: the location parameter is a
`deepObject`. An encoded `location[directory]` query selected the intended
checkout; a plain string `--param location=...` did not. The first request for
a fresh location returned an empty list; the subsequent request returned the
registered catalog. Always verify the location echoed in the response.

## Preservation and remaining scope

- Conflicting existing variants were preserved, not silently merged.
- Six promoted original directories were backed up before switching them to
  repository-backed links. Local link and backup manifests stay private.
- Unreviewed/upstream-managed libraries remain local consumers/dependencies;
  they were not bulk-added to this public repository.
- The pre-existing dirty shared checkout was not reset, cleaned, or switched.
  Its local-only consumer links and local environment files are excluded from
  accidental staging through Git's local exclude file.
- The six TorchTitan project skills were not deleted, relicensed, or replaced.
  Their generic cores, BSD notices, and project adapters require a separate
  reviewed change. Historical `alcf-job-preflight` recovery remains unverified.
- The source worktree must remain available while consumer links reference it.
  The installer refuses conflicts rather than taking ownership automatically.
