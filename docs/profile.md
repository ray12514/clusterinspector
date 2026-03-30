# Profile command

`clusterinspector profile` is the platform-profile sibling command.

Current state: implemented for local and direct-node profile collection, with batch submit still scaffolded.

The command now emits a first working system-profile artifact and keeps the submit-mode scaffold while we harden batch collection.

## Intended purpose

`profile` is focused on representative-node stack metadata, not fleet health.

Target outcomes:

- identify platform/software ownership boundaries
- infer likely externals for packaging workflows
- classify user-facing stack type
- summarize risks and upgrade blockers

## Current CLI shape

```bash
clusterinspector profile --local
clusterinspector profile --nodes gpu001
clusterinspector profile submit --scheduler slurm --partition gpu --output profiles/
```

Current behavior:

- non-submit form collects profile data and renders human, YAML, or JSON output
- `--output` writes a single artifact directly to a file
- `--output-dir` writes one artifact per profile with context-based filenames
- `--system-name`, `--site`, and `--context-name` allow artifact normalization
- submit form still prints scaffold message and exits non-zero

## Current schema baseline

The current profile schema includes:

- system identity and platform classification
- OS and scheduler facts
- hardware summary for CPU, GPU, NIC, and network fabric
- GPU topology and communication-provider hints where visible
- compiler, MPI, modules, and active context hints
- externals policy and capability-state payloads
- validation summary placeholders for future evidence integration

### Network and communication provider detection

`hardware.network` carries three fields:

- `fabric`: primary fabric type (`infiniband`, `slingshot`, `roce`, `ethernet`, `mixed`)
- `communication_provider`: optimal transport for GPU workloads on this node
- `available_providers`: all detected transports in priority order
- `mpi_provider`: MPI family (`openmpi`, `mpich`, `unknown`)

Provider detection sources are layered and graceful — missing tools produce empty results, not errors:

| Source | Command | Detects |
|--------|---------|---------|
| libfabric | `fi_info -l` | `verbs`, `cxi`, `efa`, `tcp`, `sockets` |
| UCX binary | `command -v ucx_info` | `ucx` present on PATH |
| OpenMPI transports | `ompi_info \| grep 'MCA pml'` | `ucx` as active PML (hardware transport only; `ob1`/`cm` filtered) |

Selection logic for `communication_provider`:

- UCX wins when a fast fabric (InfiniBand/RoCE/Slingshot) is present and UCX is detected — this is the GPU-aware path on Linux/OpenMPI nodes
- CXI wins on Slingshot when UCX is absent — this is the native Cray path
- Falls back through `verbs → efa → ucx → tcp → sockets` otherwise

### `mpi_gpu_aware` capability state

Upgraded from a binary `inferred/unknown` model to distinguish when a confirmed GPU transport path is in place:

- `observed`: GPU + MPI + fast fabric + (UCX or CXI detected) — transport path is confirmed passively
- `inferred`: GPU + MPI but no confirmed GPU-aware transport
- `unknown`: no GPU or no MPI

This covers both platform paths:
- Linux/OpenMPI: UCX over InfiniBand/RoCE (CUDA/ROCm memory hooks via UCX UCM)
- Cray/Slingshot: CXI over Slingshot (GPU Transport Layer)

### `active_context`

`context_name` is now populated as `prgenv_module` (Cray nodes) or `mpi_family` (Linux nodes), providing a human-readable label for the active software context.

### `observed_platform_signals`

`provider:ucx` is emitted when UCX is detected alongside the existing `provider:cxi` and `provider:verbs` signals.

## Implementation order

1. enrich with site metadata inputs and override files
2. add comparison and drift checking against checked-in profiles
3. deepen classifiers for externals, risks, and ownership
4. connect curated validation summaries more cleanly
5. harden submit-mode workflow
