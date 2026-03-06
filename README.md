# clusterinspector

`clusterinspector` is a shared inspection framework with two sibling commands:

- `clusterinspector fabric`: passive fabric discovery and health diagnosis
- `clusterinspector profile`: representative-node platform profiling

The tools are non-root, read-only, and designed to tolerate missing commands.

## Quick start

```bash
python3 -m pip install -e .
clusterinspector fabric --local
clusterinspector fabric --local --format json
```

## Current status

Implemented:

- shared core execution and parsing primitives
- fabric MVP (interfaces + PCI + driver probes, basic classification)

Scaffolded for next phases:

- deeper fabric diagnostics (RDMA/libfabric/GPU hints)
- profile command pipeline and schema
