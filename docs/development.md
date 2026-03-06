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
- `src/clusterinspector/profile/`: representative-node profile pipeline (under active build).

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

- implement `fabric/probes/rdma.py`
- implement `fabric/probes/libfabric.py`
- wire `fabric/classify/health.py` and `fabric/classify/impact.py`
- define diagnosis code catalog and message map alignment
- start `profile/schema.py` with explicit versioned fields
