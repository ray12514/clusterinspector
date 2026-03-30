# Fabric command

`clusterinspector fabric` is a passive node/fleet fabric inspector.

## Current scope

Implemented now:

- host selection via local mode, `--nodes`, `--hosts-file`, or scheduler-assisted expansion
- passive interface probe stage
- passive PCI probe stage
- passive NIC driver probe stage
- RDMA probe stage (`/sys/class/infiniband`, `/sys/class/infiniband/*/ports/*/state`, `rdma dev/link/resource`)
- libfabric provider probe stage (`fi_info -l`, `fi_info`) with provider token normalization
- health and impact classification with diagnosis codes and mapped messages
- optional GPU-path hints (`--include-gpu`) with cautious labels
- fabric classification and confidence output
- human, JSON, and Markdown formatting

In progress:

- cluster-grade validation against known-good and degraded nodes
- threshold tuning from real cluster evidence

## CLI options

```bash
clusterinspector fabric [options]
```

Key options:

- `--local`: scan current host only
- `--nodes node001,node002`: explicit host list
- `--hosts-file hosts.txt`: newline-separated hosts
- `--scheduler {none,pbs,slurm}`: host expansion helper
- `--format {human,json,markdown}`: output format
- `--summary`: include fleet summary in human output
- `--diagnose`: include diagnosis codes in human output
- `--evidence`: include evidence lines in human output
- `--workers`: SSH fanout worker count
- `--command-timeout`: per command timeout (seconds)
- `--node-timeout`: per node deadline (seconds)
- `--include-gpu`: enable cautious GPU path hint collection
- `--passive-only` / `--no-passive-only`: restrict to passive-only probes (default: `true`)

## Example usage

```bash
clusterinspector fabric --local
clusterinspector fabric --nodes node001,node002 --summary --diagnose
clusterinspector fabric --hosts-file hosts.txt --format json
clusterinspector fabric --hosts-file hosts.txt --format markdown
clusterinspector fabric --scheduler slurm --summary
clusterinspector fabric --nodes gpu001 --include-gpu --diagnose --evidence
```

## Output model

Per node fields currently include:

- `hostname`
- `primary_fabric`
- `secondary_fabrics`
- `management_fabric`
- `likely_hpc_fabric`
- `health`
- `confidence`
- `gpu_network_path`
- `diagnoses`
- `diagnosis_details`
- `evidence`

Node failures are represented in-band with:

- `ok: false`
- `error: <message>`

Fleet summary currently includes:

- `nodes_total`
- `nodes_ok`
- `nodes_error`
- `by_health`
- `by_primary_fabric`

## Diagnosis codes

Common diagnosis codes currently emitted:

- `tcp_fallback_likely`: Likely userspace fallback to TCP path
- `rdma_link_inactive`: RDMA links were detected but none appear active
- `high_speed_nic_present_no_rdmastack`: High-speed NIC detected without RDMA stack evidence
- `possible_slingshot_path`: CXI/libfabric signals suggest a possible Slingshot path
- `possible_roce_path`: Signals suggest a possible RoCE path
- `fast_path_present_but_degraded`: Fast path is present but appears degraded
- `node_unsuitable_for_multi_node_mpi`: Node likely unsuitable for multi-node MPI fast path
- `gpu_network_path_likely_host_staged`: GPU traffic is likely host-staged

## Known limitations

- GPU-path hints are heuristic and cautious by design; they do not prove runtime behavior.
- Output formats may differ in detail level during active development (`json` is canonical).
- Additional vendor-specific output variants are still expected and should be added with fixtures as observed.

## Safety expectations

- no root required
- read-only probes only
- command-level timeouts and node-level deadlines
- one node failure does not stop the fleet scan
