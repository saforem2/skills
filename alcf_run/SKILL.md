---
name: alcf-run
description: Submit PBS jobs and run commands on ALCF compute nodes (Sunspot, Aurora, Polaris). Works both from ALCF login nodes AND from a remote machine (e.g. Mac via SSH). Use when the user wants to run something on compute nodes, submit a job, or execute training on any ALCF machine — even if they're not currently on an ALCF system.
---

# ALCF Run

Run commands on ALCF compute nodes by managing PBS allocations and SSH sessions.
Works on Sunspot, Aurora, and Polaris — from login nodes or from a remote machine.

## SSH Command Selection

`kitten ssh` is preferred when `TERM=xterm-kitty` because remote hosts lack the kitty terminfo. However, `kitten ssh` only works for interactive sessions — it fails with "STDIN must be a terminal" when invoked non-interactively (e.g. from the Bash tool).

For this skill, always use `ssh` since all commands are non-interactive. Use `<SSH>` as a placeholder below (it's always `ssh`).

## Command Dispatch Convention

This skill operates in two modes based on where it's invoked:

- **Local mode** (on an ALCF login node): PBS commands run directly.
- **Remote mode** (on a Mac or other non-ALCF machine): PBS commands are wrapped in SSH to the target login node.

Throughout this skill, "run on login node" means:

| Mode | How to run `<CMD>` |
|------|-------------------|
| Local | `<CMD>` |
| Remote | `<SSH> <SSH_FLAGS> <MACHINE> '<CMD>'` |

Where `<SSH_FLAGS>` is `-A` for aurora (agent forwarding), empty for sunspot and polaris.

**Quoting rules for SSH-wrapped commands:**

- Always use `bash --login -c "..."` on the remote side so PBS tools are in PATH
- For simple commands: `<SSH> aurora 'bash --login -c "qsmert 2>&1"'`
- When grep/awk is needed, prefer piping remote output through local filters to avoid quoting hell: `<SSH> aurora 'bash --login -c "qstat -q 2>&1"' | grep -E "workq|prod|debug"`
- For compute-node SSH, single-quote the outer layer and double-quote the inner: `<SSH> <NODE> 'bash --login -c "cd /path && command"'`

## Machine Configuration

| Machine | SSH alias | Account | Filesystems | Agent forwarding |
|---------|-----------|---------|-------------|-----------------|
| Sunspot | `sunspot` | datascience | tegu:home | no |
| Aurora | `aurora` | AuroraGPT | flare:home | yes (`-A`) |
| Polaris | `polaris` | AuroraGPT | home:eagle | no |

## Workflow

### Phase 0: Detect execution mode and target machine

Determine whether we're on an ALCF login node or running remotely.

```bash
hostname
```

| Hostname matches | Mode | Machine | Source |
|-----------------|------|---------|--------|
| `sunspot-uan*` | local | sunspot | auto-detected |
| `aurora-uan*` | local | aurora | auto-detected |
| `polaris-login*` | local | polaris | auto-detected |
| anything else | remote | — | must be specified by user |

**If remote**, the user must specify the target machine (aurora, sunspot, or polaris). If not provided in the invocation, ask:

> "You're running from a remote machine. Which ALCF system do you want to target: aurora, sunspot, or polaris?"

**If remote**, validate SSH connectivity before proceeding:

```bash
<SSH> -o ConnectTimeout=10 <SSH_FLAGS> <MACHINE> 'hostname'
```

If this fails, the user likely needs to run `ssh-add` or check their `~/.ssh/config`. Report the error and stop.

**If local**, the user CAN still specify a machine name — just validate it matches the detected hostname.

### Phase 1: Check for existing allocation

Run `qsmert` on the login node to check for running PBS jobs:

**Local:**
```bash
qsmert 2>&1
```

**Remote** (use `bash --login` to ensure PBS tools are in PATH):
```bash
<SSH> <SSH_FLAGS> <MACHINE> 'bash --login -c "qsmert 2>&1"'
```

If there are running jobs with compute nodes listed, extract the first node hostname. Before using it, check if it's already busy (Phase 1b). If no running jobs, proceed to Phase 2.

#### Phase 1b: Check if allocation is in use

Before reusing an existing allocation, verify the compute node isn't already running a workload:

Local:
```bash
ssh -o StrictHostKeyChecking=no <NODE> 'ps aux | grep -E "python|mpi" | grep -v grep | grep $(whoami)' 2>&1
```

Remote:
```bash
ssh -o StrictHostKeyChecking=no <NODE> 'ps aux | grep -E "python|mpi" | grep -v grep | grep foremans' 2>&1
```

If there are running python/mpi processes, the allocation is busy. Check other running jobs, or if all allocations are busy, ask the user whether to submit a new job or wait.

### Phase 2: Submit a PBS job

Ask the user how many nodes they need (default: 2) and walltime (default: "02:00:00") if not specified.

**Step 2a: Determine queue**

Local:
```bash
qstat -q 2>&1 | grep -E "workq|prod|debug" | awk '{print $1}' | head -1
```

Remote:
```bash
<SSH> <SSH_FLAGS> <MACHINE> 'bash --login -c "qstat -q 2>&1"' | grep -E "workq|prod|debug" | awk '{print $1}' | head -1
```
The second form pipes the remote output through local grep/awk, avoiding quoting headaches.

**Step 2b: Submit job**

Use the machine-specific account and filesystems from the configuration table.

Local:
```bash
qsub -q <QUEUE> -A <ACCOUNT> -l walltime="<WALLTIME>" -l filesystems=<FILESYSTEMS> -l select=<NODES> ~/test.sh
```

Remote:
```bash
<SSH> <SSH_FLAGS> <MACHINE> 'bash --login -c "qsub -q <QUEUE> -A <ACCOUNT> -l walltime=\"<WALLTIME>\" -l filesystems=<FILESYSTEMS> -l select=<NODES> ~/test.sh"'
```

**Step 2c: Poll for job state**

Local:
```bash
qstat -f <JOBID> 2>&1 | grep "job_state"
```

Remote:
```bash
<SSH> <SSH_FLAGS> <MACHINE> 'bash --login -c "qstat -f <JOBID> 2>&1"' | grep job_state
```

Poll until `job_state = R`.

### Phase 3: Get the compute node hostname

**Primary method** — Local:
```bash
qsmert | egrep "x[1,3,4][0-9]" | awk '{print $4}' | head -1
```

**Primary method** — Remote (pipe through local awk to avoid quoting issues):
```bash
<SSH> <SSH_FLAGS> <MACHINE> 'bash --login -c "qsmert 2>&1"' | egrep "x[1,3,4][0-9]" | awk '{print $4}' | head -1
```

**Fallback (from qstat)** — Local:
```bash
qstat -f <JOBID> 2>&1 | grep exec_host | awk -F= '{print $2}' | awk -F/ '{print $1}' | tr -d ' '
```

**Fallback** — Remote (pipe through local grep/awk):
```bash
<SSH> <SSH_FLAGS> <MACHINE> 'bash --login -c "qstat -f <JOBID> 2>&1"' | grep exec_host | awk -F= '{print $2}' | awk -F/ '{print $1}' | tr -d ' '
```

**Verify SSH to compute node** (same in both modes — the SSH config's ProxyJump handles routing transparently):

```bash
<SSH> -o ConnectTimeout=10 <NODE> hostname
```

From a remote Mac, `<SSH> x4502` automatically hops through aurora via ProxyJump. No manual two-hop command needed.

### Phase 4: Determine working directory

**Local mode**: capture the current directory — it's a valid ALCF path:
```bash
pwd
```

**Remote mode**: `pwd` gives a local Mac path which doesn't exist on ALCF. Handle as follows:

1. If the user's command already includes a `cd` (e.g. `cd /path/to/project && ...`), use that and skip this step.
2. Otherwise, ask the user:
   > "You're running remotely. What directory on <MACHINE> should be the working directory? (e.g. /home/foremans/project)"
3. If the user doesn't care, default to their home directory on the ALCF machine.

### Phase 5: Run the command on the compute node

Execute the user's command via SSH to the compute node. This command is the same in both local and remote modes because the SSH config's ProxyJump handles the routing.

**Local mode:**
```bash
<SSH> <NODE> 'bash --login -c "cd <CWD> && source <(curl -fsSL https://bit.ly/ezpz-utils) && ezpz_setup_env && <COMMAND>"' 2>&1
```

**Remote mode** — explicitly set proxy env vars (bash --login may not set them correctly when the SSH chain originates from outside ALCF):
```bash
<SSH> <NODE> 'bash --login -c "export http_proxy=http://proxy.alcf.anl.gov:3128 && export https_proxy=http://proxy.alcf.anl.gov:3128 && cd <CWD> && source <(curl -fsSL https://bit.ly/ezpz-utils) && ezpz_setup_env && <COMMAND>"' 2>&1
```

For long-running commands (training runs), use `run_in_background: true` on the Bash tool.

**Monitoring note:** Some commands (e.g. `ezpz benchmark`) redirect output to log files on the compute node rather than stdout, so the SSH session's stdout stays empty. If a Monitor on the local output file shows nothing, check the compute node for log files:

```bash
<SSH> -o StrictHostKeyChecking=no <NODE> 'ls -lt <CWD>/outputs/ 2>/dev/null | head -10'
```

Then tail the remote log directly:
```bash
<SSH> -o StrictHostKeyChecking=no <NODE> 'tail -f <LOG_PATH>' | grep --line-buffered -E "step|loss|acc|Error|Took"
```

### Phase 6: Report results

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
- `~/test.sh` in SSH single-quoted commands expands on the remote shell to the ALCF home directory, which is correct

## SSH Prerequisites (for remote mode)

Remote mode requires these entries in `~/.ssh/config`:

**Login node aliases** (so `ssh aurora` works):
```
Host aurora
  HostName login.aurora.alcf.anl.gov
  User foremans
  ForwardAgent yes

Host sunspot
  HostName sunspot
  User foremans
  ProxyJump bastion

Host polaris
  User foremans
  HostName polaris.alcf.anl.gov
```

**Compute node ProxyJump** (so `ssh x4502` transparently hops through the login node):
```
Host x4*
  User foremans
  ProxyJump aurora
  ForwardAgent yes

Host x1*
  User foremans
  ProxyJump bastion,sunspot
  ForwardAgent yes

Host x3*
  User foremans
  ProxyJump polaris
  ForwardAgent yes
```

If SSH connectivity fails in Phase 0, check that these entries exist and that `ssh-add` has loaded the appropriate key.
