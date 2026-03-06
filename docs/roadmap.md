# Roadmap

This roadmap tracks how `clusterinspector` is being built into two production commands.

## Phase 1: Shared core

Status: complete (initial version).

Delivered:

- common models for command results, evidence, node/fleet report payloads
- local and SSH runners with timeout handling
- host resolution from local, explicit host lists, hosts file, or scheduler helpers
- evidence and parsing helpers

## Phase 2: Fabric MVP

Status: complete (initial usable version).

Delivered:

- interface inventory (`ip` + sysfs fallback)
- PCI NIC family hints (`lspci -nn`)
- driver enrichment (`ethtool -i`)
- initial classification for primary/secondary/likely fabric
- human and JSON outputs

Acceptance for this phase:

- `clusterinspector fabric --local` returns useful output even with missing tools
- `clusterinspector fabric --nodes ...` scans continue if one node has errors

## Phase 3: Fabric depth

Status: planned.

Planned deliverables:

- RDMA probes (`rdma dev/link/resource`, `/sys/class/infiniband`, optional verbs tools)
- libfabric provider probes (`fi_info -l`, `fi_info`)
- health scoring (`healthy`, `degraded`, `impaired`, `unknown`)
- impact diagnosis codes (for example TCP fallback and fast-path impairment)
- optional GPU-path hinting with cautious labels only

## Phase 4: Profile MVP

Status: planned.

Planned deliverables:

- profile schema v1
- system/GPU/compiler/MPI probes
- initial ownership classifier
- primary YAML output and human summary
- first working local and direct-node profile collection

## Phase 5: Profile depth

Status: planned.

Planned deliverables:

- module model probe and fabric hint reuse
- externals + stack-class + risk classifiers
- JSON and Markdown profile renderers
- batch submit workflow hardening
