---
name: alcf-run
description: Submit PBS jobs and run commands on ALCF compute nodes (Sunspot, Aurora, Polaris). Use when the user wants to run something on compute nodes, submit a job, or execute training on any ALCF machine.
---

# ALCF Run

Run commands on ALCF compute nodes by managing PBS allocations and SSH sessions.
Works on Sunspot, Aurora, and Polaris.

## Workflow

### Phase 1: Detect machine

Determine which ALCF machine we're on from the hostname:

```bash
hostname
```

| Hostname pattern | Machine | Account | Filesystems |
|-----------------|---------|---------|-------------|
| `sunspot-uan*` | Sunspot | datascience | tegu:home |
| `aurora-uan*` | Aurora | AuroraGPT | flare:home |
| `polaris-login*` | Polaris | AuroraGPT | home:eagle |

### Phase 2: Check for existing allocation

Run `qsmert` to check if there's already a running PBS job:

```bash
qsmert 2>&1
```

If there are running jobs with compute nodes listed, extract the first node hostname and skip to Phase 4.

If no running jobs, proceed to Phase 3.

### Phase 3: Submit a PBS job

Ask the user how many nodes they need (default: 2) and walltime (default: "02:00:00") if not specified.

Determine the queue dynamically:
```bash
qstat -q 2>&1 | grep -E "workq|prod|debug" | awk '{print $1}' | head -1
```

Use the machine-specific account and filesystems from Phase 1:
```bash
qsub -q <QUEUE> -A <ACCOUNT> -l walltime="<WALLTIME>" -l filesystems=<FILESYSTEMS> -l select=<NODES> ~/test.sh
```

Poll `qstat -f <JOBID>` until `job_state = R`:
```bash
qstat -f <JOBID> 2>&1 | grep "job_state"
```

### Phase 4: Get the compute node hostname

Extract from `qsmert` or `qstat -f`:
```bash
qsmert | egrep "x[1,3,4][0-9]" | awk '{print $4}' | head -1
```

If that fails (e.g. on Polaris where hostnames differ), fall back to:
```bash
qstat -f <JOBID> 2>&1 | grep exec_host | awk -F= '{print $2}' | awk -F/ '{print $1}' | tr -d ' '
```

Verify SSH connectivity:
```bash
ssh -o ConnectTimeout=10 <NODE> hostname
```

### Phase 5: Capture working directory

Before SSH'ing, capture the current working directory:
```bash
pwd
```

This will be used as the `cd` target on the compute node.

### Phase 6: Run the command

Execute the user's command on the compute node:
```bash
ssh <NODE> 'bash --login -c "cd <PWD> && source <(curl -fsSL https://bit.ly/ezpz-utils) && ezpz_setup_env && <COMMAND>"' 2>&1
```

For long-running commands (training runs), use `run_in_background: true` on the Bash tool and set up a Monitor to stream results:
```bash
tail -f <OUTPUT_FILE> | grep --line-buffered -E "step:|loss:|acc|accuracy|Error|OOM|Training starts|Took|\d{4}-\d{2}-\d{2}"
```

### Phase 7: Report results

After the command completes (or on monitor events), report:
- Timestamps and step progress
- Training metrics (tps, tflops, mfu, memory)
- Loss, accuracy, grad_norm
- Errors or OOM messages
- Total wall time

## Important Notes

- `bash --login` ensures proxy env vars are set (needed for pip, wandb, curl on compute nodes)
- `ezpz_setup_env` sets up the Python environment, PBS vars, and distributed config
- Do NOT run `pkill` or `ezpz_kill_mpi` via SSH — it can kill the SSH session's own palsd process
- If the user provides a command like `FLAVOR=moe ; CONFIG=debugmodel ; ezpz launch python3 -m ...`, wrap it exactly as given
- For environment variables before the command (e.g. `LBS=2 GAS=1`), include them in the SSH command string
- The keep-alive script `~/test.sh` must exist on the machine (it's a simple `while :; do sleep 1m; done` loop)
