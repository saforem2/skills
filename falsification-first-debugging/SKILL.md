---
name: falsification-first-debugging
description: Use when diagnosing an uncertain technical failure.
version: 1.0.0
author: Hermes
license: MIT
metadata:
  hermes:
    tags: [debugging, falsification, root-cause, verification]
---

# Falsification-First Debugging

## When to Use

Use for uncertain failures, intermittent behavior, environment-dependent bugs, or any investigation where the first plausible explanation could be wrong.

## Procedure

1. Establish execution context: hostname, cwd, repo root/HEAD, relevant network/runtime, and exact failing artifact.
2. State up to three leading hypotheses with confidence and supporting observations.
3. For each hypothesis, name the cheapest read-only command or observation that would disprove it.
4. Run those discriminating checks before changing state. Preserve raw output needed to support the diagnosis.
5. Update or reject hypotheses explicitly; never keep a favored explanation after contrary evidence.
6. Apply the narrowest reversible fix to the surviving cause.
7. Define and run an acceptance check that proves intended behavior—not merely that a command returned zero.
8. Reconfirm the target context in the same evidence set used to claim success.

## Checkpoints

After roughly five tool calls in an open-ended investigation, report compactly:
- current best hypothesis and confidence;
- facts definitively ruled out;
- fastest safe workaround available now;
- next discriminating test.

Continue autonomously unless a decision affects shared resources, irreversible state, credentials, or production resources the agent did not create.

## Rules

- Label partial-log conclusions and inferred layouts as **unverified inference**.
- Verify commands/flags locally (`command -v`, `--help`, source/docs) before recommending them.
- Do not kill live sessions, SSH masters, foreground processes, or production jobs to test a theory. Diagnose read-only first.
