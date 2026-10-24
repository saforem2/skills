---
name: generated-file-merge-conflicts
description: Fix files that conflict every time a tool regenerates them.
version: 1.0.0
author: Hermes Curator
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [git, merge-driver, gitattributes, sync, multi-host, generated-files]
    related_skills: [systematic-debugging, test-driven-development, merge-reconciler]
---

# Generated-File Merge Conflicts

## When to Use

- The same path conflicts repeatedly or on a schedule across two clones.
- A tool or plugin regenerates a tracked file on more than one machine.
- A conflict's two sides share a long identical body and differ only in
  machine-produced fields.
- You are about to hand-resolve a conflict you have already hand-resolved
  before on the same path.

Do NOT use for two humans' or two agents' deliberate edits to the same file —
that is `merge-reconciler`. Here nobody disagreed; a machine ran twice.

This is for files a tool **generates**, not files a human edited. Two clones
each create the same path from the same template, so git sees two unrelated
blobs at one path. Typical cases: daily/periodic notes, lockfiles, exported
configs, timestamped reports, scaffolded boilerplate.

## Always-on rules

- **A conflict that recurs on a schedule has a structural cause.** Resolving
  the instance leaves the generator in place and guarantees the next
  occurrence. Diagnose the generator before touching the conflict.
- **Never let an automated resolution discard human-typed content.** Any
  driver, hook, or merge strategy must fall back to a real conflict when the
  two sides disagree on prose. Write that as a test before trusting it.
- **Offer the upstream fix alongside the merge fix.** A merge driver makes
  collisions resolve cleanly; stopping one host from generating the file
  removes them. Present both and let the user choose.
- **Never propose `-X ours` / `-X theirs` as the standing fix** for this class.
  They resolve by discarding one whole side, which silently eats notes typed
  on the losing machine.
- **The driver command is local-only by design.** `.gitattributes` is
  versioned, but git deliberately refuses to take `merge.<name>.driver` from
  it, because cloning a repo would then execute arbitrary code. Ship an
  installer script and say plainly that it must run once per clone.

## Procedure

### 1. Prove the file is generated, not edited

Compare the conflicting sides. Generated collisions differ only in
machine-produced fields (resolved placeholders, timestamps, tool output blocks)
while sharing a long identical template body.

```bash
git show <commitA>:<path> > /tmp/A; git show <commitB>:<path> > /tmp/B; diff -u /tmp/A /tmp/B
```

### 2. Confirm the pattern is chronic

One collision is luck; a repeating one justifies tooling. Check mechanically
rather than trusting recall:

```bash
# Paths added more than once across all history = independently generated
git log --all --diff-filter=A --format='%H %ad' --date=short --name-only -- '<dir>/*.md'

# Prior hand-resolutions of the same class
git log --oneline --merges -20
```

### 3. Identify why the two copies differ

The divergence is usually *configuration skew* between clones, not a content
disagreement: one host has a plugin/tool the other lacks, so it post-processes
the generated file further.

Check whether the config that causes the skew is itself gitignored. If it is,
the skew is permanent and cannot be fixed by syncing settings — the merge
driver is then the correct layer.

### 4. Build the driver test-first

Write the tests before the driver (see `test-driven-development`). The suite
must contain, at minimum:

- the scaffold-only collision resolving cleanly (exit 0, no markers);
- the same case with the sides swapped, proving order-independence;
- **a genuine prose clash still conflicting** (exit 1, markers present);
- an ordinary 3-way merge with a real base still working.

The prose-clash test is the one that matters. Without it you have built
something that can eat the user's notes.

### 5. Implement the driver

Git invokes it as `driver %O %A %B %L %P`, and it must write the merged result
to `%A` and exit 0 for clean or non-zero for conflict. The working shape:

1. Try a plain 3-way merge via `git merge-file` first.
2. On conflict, retry with generated scaffolding **stripped out**, then check
   whether that normalized merge is clean.
3. If it is, the only disagreement was scaffolding: re-inflate from whichever
   side is more populated, carrying both sides' real content across.
4. Otherwise leave the conflict markers and exit non-zero.

Two implementation details that are easy to get wrong:

- **Strip scaffolding, do not substitute a placeholder token.** Replacing a
  block with `<<WAKATIME>>` makes *absent* differ from *present*, which is
  exactly the collision you are trying to neutralize. Delete the lines.
- **An add/add has an empty base, so a normalized 3-way merge still conflicts
  whenever any real content differs.** Synthesize a base from the lines both
  sides share (`difflib.SequenceMatcher.get_matching_blocks`). Because both
  copies came from one template, the common lines *are* the effective
  ancestor; this turns "two unrelated files" into "one template plus two
  independent edits", which merges cleanly when the edits are disjoint and
  still conflicts honestly when they are not.

See `references/git-merge-drivers.md` for the invocation contract and wiring.

### 6. Validate against the real historical conflict

Unit tests prove the logic; replaying the actual commits proves the fix. Feed
the two real blobs through the driver and diff the output against the
resolution a human already committed:

```bash
git show <sideA>:<path> > /tmp/A; git show <sideB>:<path> > /tmp/B; : > /tmp/O
python3 <driver> /tmp/O /tmp/A /tmp/B 7 '<path>'; echo "exit=$?"
git show <resolved>:<path> | diff -u - /tmp/A && echo IDENTICAL
```

Byte-identical output against the known-good resolution is the acceptance bar.

### 7. Wire it up and stop for consent

Commit `.gitattributes`, the driver, its tests, and an installer script. Then
**stop and ask before running the installer**, on every clone. It writes to
`.git/config`; that is a state change to the user's environment, not part of
authoring the fix.

## Pitfalls

- **Resolving the conflict and calling it done.** The generator reruns tonight.
  Ship the driver or the upstream fix, not just the resolution.
- **Assuming the two sides disagree.** Read both blobs before arbitrating; for
  generated files the content is usually identical and only tool output
  differs.
- **Trusting a clean unit-test run as proof.** Replay the real commits; the
  synthetic fixtures rarely capture the exact whitespace and trailing-newline
  shape the generator emits.
- **Committing the driver command into `.gitattributes`.** Git ignores it there
  and the driver silently never runs, so conflicts keep appearing and the fix
  looks broken.
- **Forgetting the second clone.** The driver only applies where it is
  registered; an unregistered host still produces raw conflict markers and
  pushes them.
- **Normalizing away too much.** If a rule strips a region a human also edits,
  real edits get treated as scaffolding and silently dropped. Keep the patterns
  narrow and anchored to tool-owned markers.

## Verification

- Full driver test suite green, including the prose-clash conflict test.
- Replay of the real historical collision produces output identical to the
  accepted resolution.
- `git check-attr merge -- <representative-path>` reports the driver name.
- `git config --get merge.<name>.driver` returns the command on every clone.
