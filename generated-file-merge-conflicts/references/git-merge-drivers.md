# Git merge drivers: invocation contract and wiring

Depth reference for custom merge drivers. Load when implementing or debugging
one; the SKILL.md procedure covers the decision flow.

## Invocation contract

Git calls the driver as a shell command with placeholders expanded:

| Token | Meaning |
|---|---|
| `%O` | Ancestor/base version. **Empty file for an add/add conflict.** |
| `%A` | "Ours" version. The driver MUST write its result here. |
| `%B` | "Theirs" version. |
| `%L` | Conflict-marker size (default 7). |
| `%P` | The pathname in the worktree, useful for logging. |

Exit status is the whole protocol:

- `0` — clean merge; git stages the contents of `%A`.
- non-zero — conflict; git leaves the path unmerged and expects `%A` to hold
  conflict markers for the human.

The driver owns `%A` entirely. Writing nothing on the clean path silently
empties the file.

## Why an add/add conflict cannot auto-resolve

A normal merge has three inputs: base, ours, theirs. Git computes two diffs
against the base and applies both. An add/add has **no base** — `%O` is empty —
so both sides read as "the entire file was added", every line overlaps, and the
whole file becomes one conflict hunk. No merge strategy fixes this, because the
information git needs was never recorded.

The workaround is to manufacture the missing ancestor. When both copies came
from one template, the lines they share *are* the effective ancestor:

```python
import difflib

def synthetic_base(a: str, b: str) -> str:
    a_lines, b_lines = a.splitlines(keepends=True), b.splitlines(keepends=True)
    m = difflib.SequenceMatcher(None, a_lines, b_lines, autojunk=False)
    out = []
    for blk in m.get_matching_blocks():
        out.extend(a_lines[blk.a : blk.a + blk.size])
    return "".join(out)
```

Pass `autojunk=False`. The default heuristic treats lines recurring in >1% of a
large file as junk and skips them, which throws away exactly the repeated
template scaffolding (`> `, blank lines, fence markers) you need in the base.

## Delegating the actual merge

Do not hand-roll diff3. Shell out to git and let it do the merge:

```python
subprocess.run(["git", "merge-file",
                "-L", "HEAD", "-L", "base", "-L", "incoming",
                ours_path, base_path, theirs_path])
```

Note the argument order is **ours, base, theirs** — base in the middle, not
first. The result is written in place to the first path, and the return code
follows the same clean/conflict convention as the driver's own exit status.

## Wiring

Two halves, deliberately split by git for security.

**Versioned** — `.gitattributes`, committed, travels with the repo:

```gitattributes
<path-glob> merge=<driver-name>
```

**Local-only** — `.git/config`, set per clone:

```bash
git config merge.<driver-name>.name "human readable description"
git config merge.<driver-name>.driver "python3 '/abs/path/driver.py' %O %A %B %L %P"
```

Git refuses to read the driver *command* from `.gitattributes` on purpose:
otherwise cloning any repository would execute code it carries. There is no
flag to relax this, so an installer script that each machine runs once is the
only ergonomic answer. Make the installer idempotent — it sets the same two keys
every time — and have it self-verify.

## Debugging a driver that appears not to run

Work down this list; the failure is almost always one of them.

1. `git check-attr merge -- <path>` — prints `merge: unspecified` when the
   glob does not match. `.gitattributes` patterns follow gitignore syntax, so
   `dir/*.md` does not match nested subdirectories; use `dir/**/*.md`.
2. `git config --get merge.<name>.driver` — empty means the local half was
   never installed on this clone.
3. Driver path must be **absolute**. Git runs the command from the repo root
   during a merge, but relative paths break for worktrees and submodules.
4. A driver crash (traceback, missing interpreter) exits non-zero, which git
   reads as a legitimate conflict. A driver that "never seems to work" is often
   one that is erroring on every invocation — run it by hand on two real blobs
   before blaming the wiring.
5. Merge drivers do not run during `git rebase` in all git versions, and never
   during fast-forward updates — no merge happens, so nothing invokes them.

## Testing without a repository

The driver is a pure file-in/file-out program, so tests need no git repo at
all: write three temp files, invoke the driver as a subprocess with the same
five arguments git would pass, then assert on the exit code and on the contents
of `%A`. This keeps the suite fast and makes the real-commit replay (SKILL.md
step 6) the only test that needs repository state.
