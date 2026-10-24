---
name: minimal-dependency-defect-probes
description: Isolate a defect with a stdlib-only probe first.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [debugging, reproduction, distributed, hpc, isolation]
    related_skills: [policy-weight-sync-validation]
---

# Minimal-Dependency Defect Probes

## When to Use

Use when a suspected defect lives inside a stack that is expensive or unreliable to run: a multi-node scheduler job, an actor framework, a GPU/accelerator runtime, a long-building native extension, or an environment that is currently broken for unrelated reasons.

The goal is a probe that answers one question in minutes and cannot be derailed by anything else in the stack.

## Procedure

1. **Name the mechanism, not the symptom.** Reduce the hypothesis to the specific expression that decides behavior: an environment lookup, a hostname or path comparison, a precedence ordering, a capability probe, a divisibility check. If you cannot write the deciding expression down, keep reading source until you can — a probe built on a vague hypothesis tests nothing.

2. **Reimplement only that expression, with the standard library.** No framework import, no model, no accelerator context. Print the inputs and the computed result from each participating process. A probe that imports the broken stack inherits the breakage you are trying to look past.

3. **Mirror the suspect code character for character.** Copy the real expression rather than paraphrasing it. `environ.get(KEY, default)` and `environ.get(KEY) or default` differ on empty and falsy values; a paraphrase can clear a real defect or invent one. Quote the upstream line in a comment so later readers can diff it against the source.

4. **Emit a machine-checkable verdict.** Print one structured row per process plus an explicit marker (for example `PROBE_OK` / `PROBE_BUG`) and exit nonzero on the bug. A probe whose output must be read by eye will be misread under time pressure, and it cannot gate an automated retry.

5. **Run it at the real topology.** The probe must be cheap, not unrepresentative. If the hypothesis is about cross-host behavior, run one process per host; if about rank interaction, use the real launcher. Cheap means few dependencies and a short walltime, never a reduced topology that cannot exhibit the bug.

6. **Keep the probe when the hypothesis is confirmed.** Promote it to a committed diagnostic beside the fix, with a comment recording what it measured. The next regression in the same mechanism is then one submission away.

7. **Re-prove the fix in the real stack.** The probe localizes a mechanism; it never discharges the application gate. After fixing, extend the probe to apply the fix and report before/after, then run the full end-to-end gate on the exact fixed commit.

## Always-on rules

- A passing minimal probe is evidence about the mechanism only. Never report it as the feature working; say what it proves and name the remaining gate.
- Write the probe to shared storage the compute nodes can actually read. Node-local paths such as `/tmp` exist on every node and silently resolve to a different empty directory, so the probe dies on a missing file rather than running.
- When the probe's own launcher fails before reaching the application, say so explicitly and fix the launcher. A launcher failure is not evidence about the hypothesis, and reporting it as one sends the investigation sideways.
- If the probe must substitute a non-standard launcher or runtime because the usual one is broken, label that substitution in the script and in the report, and state that it is scoped to the diagnostic. Never let a diagnostic workaround propagate into a training or acceptance launcher.
- Do not pile several hypotheses into one probe. One mechanism per probe keeps attribution intact; a combined probe that fails tells you nothing about which part failed.
