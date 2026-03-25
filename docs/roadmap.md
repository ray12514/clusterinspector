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

Status: code-complete, cluster validation pending.

Delivered so far:

- RDMA probes (`rdma dev/link/resource`, `/sys/class/infiniband`)
- libfabric provider probes (`fi_info -l`, `fi_info`)
- health scoring (`healthy`, `degraded`, `impaired`, `unknown`)
- impact diagnosis codes (including fallback/degraded/unsuitable flags)
- optional GPU-path hinting with cautious labels
- Markdown output mode
- broader parser coverage for `rdma` and `fi_info` output variants
- consistent diagnosis rendering details across human/JSON/Markdown outputs

Remaining for phase completion:

- execute cluster validation runs against known-good and known-degraded nodes
- tune thresholds/confidence based on real cluster evidence

## Phase 4: Profile MVP

Status: initial implementation landed.

Delivered so far:

- profile schema v1
- system, GPU, compiler, MPI, modules, and fabric-hint probes
- initial platform classification and capability-state payload
- YAML, JSON, and human output modes
- local and direct-node profile collection
- topology and network-provider hints
- artifact writing with context-based filenames

Remaining for phase completion:

- site metadata input and override files
- comparison and drift checking against checked-in profiles
- stronger curated validation summary integration

## Phase 5: Profile depth

Status: planned.

Planned deliverables:

- module model probe and fabric hint reuse
- externals + stack-class + risk classifiers
- JSON and Markdown profile renderers
- batch submit workflow hardening
