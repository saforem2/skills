---
name: validation-check-authoring
description: Prove validation-suite checks can fail before trusting.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [testing, validation, distributed, hpc, negative-control]
    related_skills: [test-driven-development, systematic-debugging]
---

# Authoring validation checks

For adding cases to a validation, acceptance, or conformance suite — hardware
and distributed suites especially, where a check that silently never fires is
the normal failure mode rather than a rare one.

The governing idea: **a check you have not seen fail is not evidence.** Most of
this skill is about closing the gap between "the suite is green" and "the suite
would have caught the thing it claims to catch."

## When to Use

Use when:

- adding a case to an existing validation/acceptance/conformance suite;
- writing a check that must hold across processes, ranks, nodes, or devices;
- validating an integration whose component version floats independently of
  the platform (user-installed, vendored, side-loaded);
- a suite is green and you need to establish whether that means anything.

Not for ordinary unit-test authoring against local code — use
`test-driven-development` for the RED-GREEN-REFACTOR loop.

## Procedure

### 1. Read the harness contract before writing a case

Read the manifest/registry format, an existing case of the same shape, and the
harness's own unit tests. Match the established structure rather than inventing
a parallel one.

Run the harness's test suite on the **unmodified** tree first and record which
tests already fail. Without that baseline you cannot tell your change from
pre-existing breakage, and you will either chase someone else's bug or take
blame for it. Report pre-existing failures as pre-existing.

### 2. Declare prerequisites so absence skips instead of failing

Declare every required command, module, and resource the harness supports. A
case whose optional dependency is missing must **skip**, not fail: a suite that
fails an acceptance run over a component the platform never shipped trains its
readers to ignore red.

Distinguish the three states explicitly in output — component absent, component
present but unusable, component present and wrong. They have different owners.

### 3. Check results, not the absence of an exception

"The call returned" is the weakest possible assertion. Prefer checks with a
closed form or an invariant the system cannot satisfy by accident:

- values agree with an independent source (the launcher/environment, a second
  API, ground truth) rather than only with themselves;
- identifiers form the complete set they should (a permutation of a known
  range) — this catches duplicates, which typically raise nothing;
- resources that must be exclusive are actually distinct across participants;
- a computation returns the mathematically required answer, not merely a
  finite one.

The silent failures are the ones worth the code. A configuration error that
raises will be found by any smoke test; one that quietly degrades throughput or
correctness will not.

### 4. Prove every check can fail — the step that is actually skipped
For each assertion that matters, inject the exact fault it targets and confirm
the suite fails **with that check's specific message**. Grep the log for the
message; do not accept a nonzero exit as proof, because an unrelated early
error also exits nonzero and looks identical from outside.

```bash
<inject fault> <run case> >neg.log 2>&1
rc=$?
if   [ $rc -eq 0 ];                               then echo "BAD: check is inert"
elif grep -q "<expected assertion text>" neg.log; then echo "ok: right reason"
else echo "BAD: failed, but not via the check"; fi
```

Prefer an injection that leaves the system **in the configuration under test**.
Removing or hiding the resource often makes a lower layer reject the setup
earlier and more loudly, which aborts before your check runs — the control then
passes for the wrong reason. To prove a per-participant resource-binding check,
force the duplicate assignment while leaving all resources visible.

Re-run the injection whenever the dependency under test changes version. A
library that starts validating a configuration it previously accepted is an
improvement in the library and a silent no-op in your control.

Keep fault injection in the external driver — environment overrides, wrapper
flags — not as a test-only branch inside shipped source, so what runs in the
negative control is the same code that runs in production.

### 4a. Address the check to the layer you mean to test

When a command is invoked through a wrapper — a launcher, a runner, a shim —
introspection flags are consumed by the **outermost** parser that recognizes
them. `launcher run ... -- app --help` returns the launcher's help, not the
app's. A gate that then greps the captured output for the app's options fails
while proving nothing about the app, and the failure looks like an application
incompatibility.

Invoke each layer separately and capture each to its own artifact:

```bash
launcher --help            > "$OUT/launcher-help.txt"
"$VENV/bin/python" -m app <exact argv> --help > "$OUT/app-help.txt"
```

The same trap applies to any pass-through boundary: shell wrappers, `uv run`,
`srun`/`mpiexec`, and container entrypoints all parse before the payload sees
argv.

### 4b. Grep only a stream the evidence actually reaches

Before gating on `grep <token> "$LOG"`, confirm that token is emitted to that
stream. Metrics handed to an experiment tracker, a TensorBoard writer, or a
structured sink frequently never appear on stdout, so the gate can never pass:
every healthy run is marked invalid and the wrapper exits nonzero. This is the
same inert-check failure as an untested assertion, inverted — it fires always
instead of never, and it is equally uninformative.

Count occurrences on both sides before trusting the predicate:

```bash
grep -c "<token>" "$LOG"                 # the stream the gate reads
grep -rc "<token>" "$RUN_DIR"/*.wandb    # where the metric actually lands
```

When the required evidence lives only in the tracker, either emit a bounded
local diagnostic alongside it or move the gate to an artifact that exists on
disk — a checkpoint shard count, a terminal metric line, a post-hoc adjudicator
reading the run directory. Prefer the post-hoc adjudicator when the arms are
already queued: rewriting a marker predicate is not worth destroying a queue
position, and the same script can re-judge every completed arm uniformly.

A false `INVALID` is not a scientific result. When terminal evidence shows the
run completed its steps with finite metrics and exited zero, say the predicate
is wrong rather than reporting the run as failed.

### 5. Use stable keys for cross-process grouping

Any key used to group or compare across processes must come from a stable
digest (`hashlib.blake2b`, an explicit ID), never Python's builtin `hash()` on
a string. Hash randomization differs per process, so each participant derives a
different key for the same entity, every participant looks unique, and
per-group collision checks pass vacuously while reporting confident success.

This failure is invisible in the pass output unless the check also prints the
grouping it inferred. Print it — `N groups, members/group [...]` — so a wrong
grouping is legible without a debugger.

### 6. Cover each entry point that resolves configuration differently

When several launchers, drivers, or front ends can invoke the system, each one
that discovers its configuration by a different mechanism is its own case. One
passing does not imply the others, because they exercise disjoint resolution
paths. Registering only the convenient one leaves the path most users actually
take untested.

For a launcher that derives topology itself, exercise both the explicit form
(reproducible at any size) and the derive-it-yourself form (what production
uses).

### 7. Validate on the real target, then iterate there

Run the new case on the actual target — real hardware, real scheduler, real
multi-process launch — before considering it done. Local and single-process
runs do not exercise the environment discovery, resource binding, or
cross-process grouping that these checks exist to verify; expect the first real
run to expose defects in the *test*, not the system.

Each iteration costs a queue wait, so batch scenarios into one driver run:
smoke, each launcher, multi-node, single-node, and the negative control
together, each reporting its own return code plus one overall status.

When the target sits behind a batch scheduler, see
`references/batch-scheduler-drivers.md` for job-script pitfalls that produce
false results (notably `set -u` versus `module load`, and suppressed module
output causing an instant empty-log failure).

### 8. Report findings against a current dependency

Before writing up any failure as a defect, establish the installed version of
the component under test and compare it with current upstream. A stale install
faithfully reproduces bugs fixed long ago; publishing those as current findings
is worse than not testing, because it sends readers after defects that no
longer exist.

This applies whenever a component's version floats independently of the
platform it is tested against — anything user-installed, vendored, or
side-loaded. Have the suite print the version and resolved path as its first
output so the question is answered in every log, and say in the docs which
version the cases were validated against.

Watch for a shadowing entry point: an older console script earlier on `PATH`
can win over a freshly installed one, so the version you verified is not the
one that ran.

## Always-on rules

- A gate's own assertions are part of the system under test. When a gate fails,
  first establish whether the *subject* failed or the *assertion* was wrong;
  three consecutive gate reruns that each fail on a different assertion bug are
  a sign the gate was never exercised, not that the subject is unstable.
- Before gating on a grep, verify the token reaches the stream you are reading.
  A predicate keyed to tracker-only or sink-only output can never pass and
  marks every healthy run invalid.
- Assert on the exit status of the exact invocation whenever the invocation
  itself is the proof. A command that accepts an argv and exits zero has proven
  the argv; grepping its output for a canonical option name additionally
  requires that name to be stable, which configuration-dependent transforms can
  silently break.
- Never describe a check as verified until you have watched it fail on the
  fault it targets, by its own message.
- A negative control that exits nonzero for an unverified reason is a failed
  control. Grep for the expected assertion text.
- Missing optional dependency → skip. Never fail an acceptance run over a
  component the platform does not ship.
- Print the inferred grouping, resolved topology, and component version in the
  pass path, not only on failure — a vacuous pass is otherwise indistinguishable
  from a real one.
- Distinguish the check's own bugs from the system's. On a first real-target
  run, suspect the test first.
- Fault injection belongs in the driver, not behind a flag in shipped source.
- Do not report a component's failure as a platform defect before re-running
  against current upstream.
- Record in the suite's docs which version each case was validated against, and
  which fault injection proved the check non-vacuous, so the next author can
  re-verify instead of trusting it.
