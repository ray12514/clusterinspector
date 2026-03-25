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

## Implementation order

1. enrich with site metadata inputs and override files
2. add comparison and drift checking against checked-in profiles
3. deepen classifiers for externals, risks, and ownership
4. connect curated validation summaries more cleanly
5. harden submit-mode workflow
