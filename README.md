# clusterinspector

`clusterinspector` is a shared inspection framework with two sibling commands:

- `clusterinspector fabric`: passive fabric discovery and health diagnosis
- `clusterinspector profile`: representative-node platform profiling

Both commands are designed to be non-root, read-only, and resilient when some tooling is missing on a node.

## Project status

- `fabric` is usable now with interface/PCI/driver/RDMA/libfabric probe stages, health+impact diagnosis, and human/JSON/Markdown output.
- `fabric` Phase 3 is code-complete; real-cluster validation is the remaining completion gate.
- `profile` now emits a first working system-profile artifact with local/direct-node collection, YAML/JSON/human output, topology and network hints, and artifact-writing support.
- `profile submit` remains scaffolded while batch profiling is hardened.

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
  - Current: local/SSH/scheduler host resolution, passive probe stages, diagnosis rendering across human/JSON/Markdown, optional GPU-path hints.
  - Next: complete real-cluster validation matrix and threshold tuning from observed evidence.
- `clusterinspector profile`
  - Current: working representative-node profile collection with YAML/JSON/human/markdown output and file-writing support.
  - Next: site metadata inputs, comparison/drift checks, and submit-mode hardening.

### Profile command options

```bash
# Output formats
clusterinspector profile --local
clusterinspector profile --local --format yaml
clusterinspector profile --local --format json
clusterinspector profile --local --format markdown

# Remote node
clusterinspector profile --nodes gpu001
clusterinspector profile --nodes gpu001,gpu002

# Write to file or directory
clusterinspector profile --local --output profile.yaml
clusterinspector profile --local --output-dir profiles/

# Artifact normalization overrides
clusterinspector profile --local --system-name mycluster --site mysite --context-name openmpi-cuda12

# Batch (scaffolded, not yet active)
clusterinspector profile submit --scheduler slurm --partition gpu --output profiles/
```

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
