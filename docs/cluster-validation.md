# Cluster validation playbook

Use this playbook to validate `clusterinspector fabric` against real cluster behavior.

## Goals

- verify classification on known-good fast-path nodes
- verify degraded/impaired diagnosis on intentionally problematic nodes
- verify graceful handling on Ethernet-only or tooling-limited nodes
- gather evidence payloads to tune confidence and thresholds

## Test matrix

Run at least one node from each class:

1. fast-path healthy (IB/Slingshot/RoCE expected healthy)
2. fast-path degraded (known inactive RDMA links or provider mismatch)
3. Ethernet-only or management-only node
4. GPU node with topology tooling available (`--include-gpu`)

## Commands

Use JSON as the source of truth during validation.

```bash
clusterinspector fabric --nodes nodeA,nodeB --format json --diagnose --evidence > run1.json
clusterinspector fabric --nodes gpu001 --include-gpu --format json --diagnose --evidence > run_gpu.json
clusterinspector fabric --hosts-file hosts.txt --format markdown --summary > run.md
```

## What to check

- **Classification:** `primary_fabric`, `likely_hpc_fabric`
- **Health:** `health` vs expected node condition
- **Impact:** diagnoses include expected fallback/degraded signals
- **Evidence:** sufficient probe evidence exists for each diagnosis
- **Resilience:** failures on one node do not abort remaining nodes

## Artifact capture

For each run, capture:

- command used
- output JSON/Markdown
- scheduler context (if used)
- node role/class and expected condition
- mismatches between expected and observed classification

## Tuning loop

When mismatches are found:

1. identify which probe evidence is missing/noisy
2. update parser or thresholds
3. add fixture tests for the observed output form
4. rerun validation on the same node set
