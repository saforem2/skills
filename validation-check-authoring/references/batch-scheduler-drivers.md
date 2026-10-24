# Driving a validation suite from a batch scheduler

When the real target is behind a queue, the driver script is itself a source of
false results. These pitfalls each produce a failure that looks like something
else.

## Job-script shell setup

**Do not use `set -u` in a script that runs `module load`.** Lmod's bash init
dereferences unset variables (for example `ZSH_EVAL_CONTEXT`) and aborts the
job with `unbound variable` before any payload runs. Use `set -o pipefail`
alone.

**Never redirect `module load` output to `/dev/null` behind a `|| exit` guard.**
Module systems write ordinary advisory warnings to stderr and can return
nonzero for them, so the guard kills the job while the suppression hides the
reason. The signature is a job that terminates in roughly one second with an
empty log — an unfalsifiable result. Let module output reach the log.

These two interact: a job that dies instantly with no output has usually hit
one of them, not a defect in the thing under test.

## Diagnosing an instant, empty-log failure

Run a minimal probe job that echoes a marker after each setup line — working
directory, nodefile read, module load, interpreter path, one import. The last
marker printed localizes the failure immediately. This is much cheaper than
re-reading the driver looking for the bug.

## Batching scenarios per allocation

Each submission costs a queue wait, so a one-scenario-per-job loop makes
iteration unusable. Put every scenario in one driver: smoke, each launcher,
multi-node, single-node, and the negative control. Give each its own return
code plus one aggregate status.

```bash
rc_total=0
check() { echo "RC_$1=$2"; if [ "$2" -ne 0 ]; then rc_total=1; fi; }

<scenario>; check SCENARIO_NAME $?
...
echo "OVERALL=${rc_total}"
exit "${rc_total}"
```

Grep the log for `^RC_|^OVERALL` to read the whole matrix at a glance.

The negative control needs different handling from the positive scenarios:
nonzero is required, and it must be nonzero *for the right reason*. Capture its
output to its own file and grep for the expected assertion text — see the
parent skill's step 4.

## Writing the driver

Write and validate the script locally (`bash -n`, `shellcheck`), then `scp` it.
Building it through nested local-shell → SSH → remote-heredoc quoting mangles
the content and wastes turns on quoting bugs that are not the task.

Non-interactive SSH may not initialize `PATH` for scheduler clients, so run
remote scheduler commands through a login shell (`ssh HOST 'bash -lc "..."'`)
or use the site's absolute binary path.

## Reading results

Scheduler `Exit_status=0` means the wrapper returned zero, not that the suite
passed. Always pair the scheduler record with the job artifact and the suite's
own aggregate marker. Conversely, a nonzero exit with a clean `OVERALL=0` in
the log usually means a trailing command in the wrapper failed after the suite
succeeded.
