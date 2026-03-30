# Development guide

## Environment

```bash
python3 -m pip install -e .
```

Run tests:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

Run local fabric smoke test:

```bash
PYTHONPATH=src python3 -m clusterinspector.cli fabric --local --summary
PYTHONPATH=src python3 -m clusterinspector.cli fabric --local --format json
```

## Architecture notes

- `src/clusterinspector/core/`: reusable execution, timeout, host resolution, evidence, parsing primitives.
- `src/clusterinspector/fabric/`: fleet-oriented passive diagnosis pipeline.
- `src/clusterinspector/profile/`: representative-node profile pipeline and system-profile artifact emitter.

Execution model:

- orchestrators own stage order and error isolation
- probes return normalized data + evidence
- classifiers map evidence into operator-facing labels
- outputs are pure renderers from canonical report objects

## Design constraints

- non-root, read-only collection only
- tolerate missing tools and partial evidence
- keep machine-readable outputs stable across phases
- avoid scheduler lock-in in shared core abstractions

## Suggested near-term tasks

- run `docs/cluster-validation.md` on known-good and degraded cluster nodes
- add parser fixtures for any newly observed `rdma` or `fi_info` output variants
- tune health/confidence thresholds with captured cluster evidence
- continue Profile Phase 4 depth work after Phase 3 validation closes
- validate UCX/ompi_info probe output on real InfiniBand + OpenMPI + UCX nodes
- validate CXI path on Cray/Slingshot nodes (confirm `mpi_gpu_aware: observed` fires)
- capture `ompi_info | grep 'MCA pml'` output variants for parser fixture coverage
