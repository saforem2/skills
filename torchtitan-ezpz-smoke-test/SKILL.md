---
name: torchtitan-ezpz-smoke-test
description: Run smoke tests for torchtitan-ezpz experiments (agpt, moe) on ALCF compute nodes and write benchmark reports. Use when the user wants to smoke-test model configs, verify training works, or generate benchmark results.
---

# TorchTitan-ezpz Smoke Test

Run 50-step smoke tests for torchtitan-ezpz experiment configs on ALCF compute
nodes, then write a structured benchmark report.

## Argument Parsing

Parse the user's arguments to determine what to run:

| Invocation | What runs |
|---|---|
| (no args) | agpt {debugmodel, 2b} + moe {debugmodel, 2b} |
| `--agpt` | agpt {debugmodel, 2b} |
| `--agpt <model> [model2 ...]` | agpt with specified model(s) |
| `--moe` | moe {debugmodel, 2b} |
| `--moe <model> [model2 ...]` | moe with specified model(s) |
| `--agpt ... --moe ...` | both, with their respective models |

Valid agpt models: debugmodel, 2b, 7b, 8b, 20b, 50b, 80b, 80b_alt, 80b_wide, 80b_deep, 80b_deep_alt
Valid moe models: debugmodel, 500m, 2b, 4b, 7b, small, 10b_2b, 10b_2b_sdpa, 16b

Config function names:
- agpt: `agpt_<model>` (e.g. `agpt_2b`, `agpt_debugmodel`)
- moe: `moe_<model>` (e.g. `moe_2b`, `moe_debugmodel`, `moe_10b_2b_sdpa`)

## Workflow

### Phase 1: Detect machine

```bash
hostname
```

| Hostname pattern | Machine | Account | Filesystems |
|-----------------|---------|---------|-------------|
| `sunspot-uan*` | Sunspot | datascience | tegu:home |
| `aurora-uan*` | Aurora | AuroraGPT | flare:home |
| `polaris-login*` | Polaris | AuroraGPT | home:eagle |

### Phase 2: Check for existing allocation

```bash
qsmert 2>&1
```

If running jobs exist with compute nodes listed, extract the first node
hostname and skip to Phase 4.

If no running jobs, proceed to Phase 3.

### Phase 3: Submit a PBS job

Ask the user how many nodes they need (default: 2) and walltime (default:
"02:00:00") if not specified.

```bash
qstat -q 2>&1 | grep -E "workq|prod|debug" | awk '{print $1}' | head -1
```

```bash
qsub -q <QUEUE> -A <ACCOUNT> -l walltime="<WALLTIME>" -l filesystems=<FILESYSTEMS> -l select=<NODES> ~/test.sh
```

Poll `qstat -f <JOBID>` until `job_state = R`.

### Phase 4: Get compute node and working directory

Extract node hostname from `qsmert` or `qstat -f`:
```bash
qsmert | egrep "x[1,3,4][0-9]" | awk '{print $4}' | head -1
```

Fallback:
```bash
qstat -f <JOBID> 2>&1 | grep exec_host | awk -F= '{print $2}' | awk -F/ '{print $1}' | tr -d ' '
```

Verify SSH:
```bash
ssh -o ConnectTimeout=10 <NODE> hostname
```

Capture working directory:
```bash
pwd
```

### Phase 5: Run each config sequentially

For each (module, config) pair, run a 50-step smoke test.

**Build the training command:**
```bash
ssh <NODE> 'bash --login -c "export http_proxy=http://proxy.alcf.anl.gov:3128 && export https_proxy=http://proxy.alcf.anl.gov:3128 && cd <CWD> && source <(curl -fsSL https://bit.ly/ezpz-utils) && ezpz_setup_env && ezpz launch python3 -m torchtitan.experiments.ezpz.train --module ezpz.<MODULE> --config <CONFIG> --training.steps 50 --checkpoint.no_enable <EXTRA_ARGS>"' 2>&1
```

Where:
- `<MODULE>` is `agpt` or `moe`
- `<CONFIG>` is the config function name (e.g. `agpt_2b`, `moe_500m`)
- `<EXTRA_ARGS>`:
  - For moe configs 7b and larger (7b, 10b_2b, 10b_2b_sdpa, 16b, small):
    add `--activation_checkpoint.mode none` to avoid the known
    CheckpointError from MoE routing non-determinism during AC recomputation

**Execution:**
- Run each config with `run_in_background: true` on the Bash tool
- Set up a Monitor to stream training metrics:
  ```bash
  tail -f <OUTPUT_FILE> | grep --line-buffered -E "step:|loss:|Error|OOM|Traceback|memory:|tps:|tflops:|mfu:|Took|finished|ABORT|killed|CheckpointError"
  ```
- Wait for completion before starting the next config
- If a config fails, record the error and continue to the next one

**Metrics to collect per config (from the output):**

| Metric | How to find |
|--------|-------------|
| Total/dense/sparse/active params | grep for "Total parameter count:" |
| Model name and total params | grep for "Model:" and "total parameters" |
| Peak FLOPS | grep for "Peak FLOPS used for computing MFU" |
| Final loss | last "step:" line, extract loss value |
| TPS, TFLOPS, MFU | last 5 "step:" lines, use values from the last one |
| Memory | last "step:" line, extract memory value |
| Wall time | grep for "Executing finished in" or "Took.*seconds to run" |
| W&B URL | grep for "View run.*at:" |
| Exit code | from background task completion status |
| AC mode | what was passed (full or none) |

### Phase 6: Write benchmark report

For each module that was tested, generate a report file at:
```
torchtitan/experiments/ezpz/docs/experiments/<module>/<machine>/<TIMESTAMP>-smoke-n<NODES>.md
```

Where:
- `<module>` = `agpt` or `moe`
- `<machine>` = `aurora`, `sunspot`, or `polaris` (lowercase)
- `<TIMESTAMP>` = `YYYYMMDD-HHMMSS` from the first config's start time
- `<NODES>` = number of compute nodes

The report should follow this structure:

```markdown
# <Module> Smoke Test -- <Machine> <N>-node (<Date>)

## Environment
(table: date, commit, machine, job ID, nodes, devices, steps, dataset, backend, compile)

## Model Configurations
(table: config, total params, active params, active %, layers, experts/heads, dim, LBS, seq_len)

## Results
(table: config, final loss, memory, TPS, TFLOPS, MFU, wall time, AC mode, W&B link, status)

## Known Issues
(any errors encountered, with tracebacks if applicable)
```

For moe reports, also include the MFU discussion sections:
- How MFU is computed (active params formula)
- Dense-equivalent MFU comparison table
- Detailed parameter breakdown table (dense/sparse/active)

Get the current git commit:
```bash
git rev-parse --short HEAD
```

### Phase 7: Update the module README index

Add a row to the module's README at:
```
torchtitan/experiments/ezpz/docs/experiments/<module>/README.md
```

Add a new row to the appropriate machine section table:
```markdown
| <date> | [<description>](<machine>/<filename>) | <configs tested> | <nodes> | <key result> |
```

If the machine section doesn't exist yet, create it.

### Phase 8: Print summary

Print a summary table of all results to the conversation, plus the path to the
generated report file(s).

## Important Notes

- `bash --login` ensures proxy env vars are set on compute nodes
- `ezpz_setup_env` sets up the Python environment, PBS vars, and distributed config
- Do NOT run `pkill` or `ezpz_kill_mpi` via SSH
- If a config hangs for more than 10 minutes without producing step output
  after compilation, consider it stuck and stop it
- The `~/test.sh` keep-alive script must exist on the machine
- Always create the report directory with `mkdir -p` before writing the report
- When running both agpt and moe, write separate report files for each
