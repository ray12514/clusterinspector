# Profile command

`clusterinspector profile` is the platform-profile sibling command.

Current state: scaffolded, not implemented yet.

The command shape is present now so we can keep CLI and packaging stable while implementing probe/classification stages.

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

- non-submit form prints scaffold message and exits non-zero
- submit form prints scaffold message and exits non-zero

## Planned schema baseline

The first profile schema version targets:

- platform identity (`system_name`, `vendor`, `node_class`, scheduler)
- hardware summary (GPU, NIC)
- ownership model (`vendor`, `site`, `mixed`, `unknown`)
- compiler and MPI environment hints
- module model hints
- likely externals (`required`, `buildable`, `reason`)
- stack class
- gaps/risks/blockers
- profile status (`draft`, `partial`, `validated`, `stale`)

## Implementation order

1. schema and orchestrator data flow
2. system/GPU/compiler/MPI probe stages
3. ownership + YAML output
4. modules/fabric reuse + externals + risks
5. submit-mode hardening
