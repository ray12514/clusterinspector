# clusterinspector

`clusterinspector` is a shared inspection framework with two sibling commands:

- `clusterinspector fabric`: passive fabric discovery and health diagnosis
- `clusterinspector profile`: representative-node platform profiling

Both commands are designed to be non-root, read-only, and resilient when some tooling is missing on a node.

## Project status

- `fabric` is usable now for passive interface, PCI, and driver inspection.
- `profile` is scaffolded and intentionally returns "not implemented yet" while we build it in phases.

## Install and run

```bash
python3 -m pip install -e .
clusterinspector fabric --local
clusterinspector fabric --local --format json
```

Remote examples:

```bash
clusterinspector fabric --nodes node001,node002 --summary --diagnose
clusterinspector fabric --hosts-file hosts.txt --format json
clusterinspector fabric --scheduler slurm --summary
```

## Command overview

- `clusterinspector fabric`
  - Current: local/SSH/scheduler host resolution, passive probe stages, human/JSON output.
  - Next: RDMA/libfabric/GPU hint stages, richer health and impact diagnosis.
- `clusterinspector profile`
  - Current: CLI scaffold, planned submit mode scaffold.
  - Next: schema-driven profile collection, ownership and externals classification.

## Repository layout

```text
clusterinspector/
  pyproject.toml
  README.md
  docs/
  src/clusterinspector/
    core/
    fabric/
    profile/
  tests/
```

## Documentation

- `docs/roadmap.md`: phased implementation plan and acceptance targets
- `docs/decisions.md`: architecture decisions and rationale log
- `docs/adr-template.md`: template for detailed architecture decision records
- `docs/adr/`: long-form ADRs for major design choices
- `docs/fabric.md`: fabric command behavior, options, and output model
- `docs/cluster-validation.md`: real-cluster validation matrix and test workflow
- `docs/profile.md`: profile command target schema and rollout plan
- `docs/development.md`: development workflow, testing, and architecture notes
