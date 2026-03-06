# Fabric command

`clusterinspector fabric` is a passive node/fleet fabric inspector.

## Current scope

Implemented now:

- host selection via local mode, `--nodes`, `--hosts-file`, or scheduler-assisted expansion
- passive interface probe stage
- passive PCI probe stage
- passive NIC driver probe stage
- RDMA probe stage (`/sys/class/infiniband`, `rdma dev/link/resource`)
- libfabric provider probe stage (`fi_info -l`, `fi_info`)
- health and impact classification with diagnosis codes
- optional GPU-path hints (`--include-gpu`) with cautious labels
- fabric classification and confidence output
- human, JSON, and Markdown formatting

In progress:

- broader parser coverage for diverse vendor output variants
- cluster-grade validation against known-good and degraded nodes

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

- `tcp_fallback_likely`
- `rdma_link_inactive`
- `high_speed_nic_present_no_rdmastack`
- `possible_slingshot_path`
- `possible_roce_path`
- `fast_path_present_but_degraded`
- `node_unsuitable_for_multi_node_mpi`
- `gpu_network_path_likely_host_staged`

## Known limitations

- GPU-path hints are heuristic and cautious by design; they do not prove runtime behavior.
- Output formats may differ in detail level during active development (`json` is canonical).
- Vendor-specific output variants for `rdma` and `fi_info` are still being broadened.

## Safety expectations

- no root required
- read-only probes only
- command-level timeouts and node-level deadlines
- one node failure does not stop the fleet scan
