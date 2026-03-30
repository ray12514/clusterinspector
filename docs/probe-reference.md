# Probe Reference

This document explains every command `clusterinspector` runs on a node: why it is run, what is parsed from the output, and how the result flows into the conclusions shown in the profile or fabric report.

All probes are passive and read-only. No root access is required. If a tool is not present on a node, the probe returns empty data — never an error. Commands are executed via the same `Runner` abstraction for both local and SSH execution, so the probe logic is identical in both modes.

---

## Profile command probes

### System identity (`probe_system`)

| Command | Why | What we extract |
|---------|-----|-----------------|
| `hostname -f` | Get the fully-qualified domain name | Short hostname (before first `.`) goes to `system.name`; domain suffix goes to `system.site` (e.g. `node01.hpc.example.com` → site `hpc.example.com`). Returns `unknown` if FQDN has no domain. |
| `cat /etc/os-release` | OS identity | `ID` → `os.distro`; `VERSION_ID` → `os.version`. Standard on all modern Linux distributions. |
| `uname -r` | Kernel version | Raw kernel string → `os.kernel`. |
| `getconf GNU_LIBC_VERSION` | glibc version | Strips the `glibc ` prefix → `os.glibc_version`. Relevant for ABI segmentation and Spack builds. |
| `lscpu` | CPU summary | Parses `Model name` → `hardware.cpu.model`; `Socket(s)` → `hardware.cpu.sockets_per_node`. |
| Scheduler detection (inline shell) | Detect active job scheduler | Checks `$SLURM_JOB_ID` and `command -v sinfo` → `slurm`; checks `$PBS_JOBID` and `command -v pbsnodes` → `pbs`; else `unknown`. Sets `scheduler.type` and infers `scheduler.launcher_in_alloc` (`srun` for Slurm, `mpirun` for PBS). |

---

### Cray PE detection (`probe_compiler`)

| Command | Why | What we extract |
|---------|-----|-----------------|
| `printf "PE_ENV=%s\nCRAYPE_VERSION=%s\n" "$PE_ENV" "$CRAYPE_VERSION"` | Read Cray PE environment variables | `PE_ENV=nvidia` → `prgenv_module: PrgEnv-nvidia`. Any non-empty `CRAYPE_VERSION` → `is_cray: true`. Both variables are set automatically by the Cray PE module system when a `PrgEnv-*` module is loaded. |
| `command -v cc CC ftn mpicc mpicxx mpifort gcc g++ gfortran` | Detect available compiler wrappers | Checks which compiler frontends are on `PATH`. `{cc, CC, ftn}` → `wrapper_family: cray_wrappers` (Cray PE wrappers); `{mpicc, mpicxx, mpifort}` → `wrapper_family: direct_mpi_wrappers`; anything else → `other` or `unknown`. |

**Why this matters:** `is_cray` is the pivot for the entire platform classification. It drives:
- `platform_class` → `cray-nvidia` vs `linux-nvidia` (or `cray-amd` vs `linux-amd`)
- `environment_model` → `cray_pe` vs `direct_mpi`
- `gpudirect_rdma` → Cray CXI GTL path is considered confirmed GPU RDMA evidence

**Nothing is hardcoded.** The tool does not check hostnames, cluster names, or `/etc/cray-release`. It only reads what the node's environment tells it.

---

### GPU detection (`probe_gpu`)

| Command | Why | What we extract |
|---------|-----|-----------------|
| `nvidia-smi --query-gpu=name --format=csv,noheader` | Enumerate NVIDIA GPUs | One line per GPU → model name; line count → `count_per_node`. If this command is absent or returns nothing, NVIDIA is not assumed. |
| `nvidia-smi --query-gpu=compute_cap --format=csv,noheader` | CUDA compute capability | e.g. `8.0` for A100, `9.0` for H100/H200. Needed for CUDA architecture targeting in Spack builds. |
| `nvidia-smi topo -m` | GPU interconnect and GPU-to-NIC topology | Prints a matrix of proximity tokens between GPUs and NICs. Token meanings: `NVL`/`NVC`/`NV#` → NVLink (high-bandwidth GPU fabric); `PIX` → same PCIe switch; `PXB` → different switch, same root complex; `PHB` → PCIe host bridge; `SYS`/`SOC` → traffic crosses the CPU/system memory bus (host-staged). GPU↔NIC row tokens directly determine whether GPU memory can reach the NIC without CPU involvement. |
| `rocm-smi --showproductname` | Enumerate AMD GPUs | Parses `Card series:` lines → model name and count. |
| `rocm-smi --showtopotype --showtoponuma` | AMD GPU interconnect topology | Looks for `XGMI` tokens → `interconnect_type: xgmi`; `PCIe` → `pcie`. NUMA node assignments extracted for `numa_affinity`. |
| `lsmod \| grep -E 'nvidia_peermem\|nv_peer_mem'` | GPUDirect RDMA kernel module | `nvidia-peermem` (or the older `nv_peer_mem`) is the kernel module that enables the NVIDIA GPU to register memory regions directly with the RDMA subsystem. Its presence means the kernel supports GPU↔NIC DMA without CPU staging. Absence does not prove it is broken — it may just not be loaded yet. |

**How `gpudirect_rdma` is classified:**

| Evidence | State |
|----------|-------|
| `nvidia-peermem`/`nv_peer_mem` module loaded | `observed` |
| Cray node (`is_cray: true`) with `cxi` provider (Cray GTL provides GPU RDMA natively over Slingshot) | `observed` |
| GPU + fast fabric + topology shows PIX/PXB/NV between GPU and NIC (structurally direct, driver not confirmed) | `inferred` |
| GPU + fast fabric + topology shows SYS/SOC (CPU-staged, e.g. LIQID PCIe-switched nodes) | `unknown` |
| No GPU or no fast fabric | `unknown` |

This means a LIQID machine with GPU + InfiniBand but CPU-staged topology will correctly show `gpudirect_rdma: unknown` instead of the misleading `observed` that a naive GPU+fabric check would produce.

---

### Network fabric and provider detection (`probe_fabric_hints`)

| Command | Why | What we extract |
|---------|-----|-----------------|
| `for n in /sys/class/net/*; do basename "$n"; done` | List all network interfaces | Interface names from the kernel's network subsystem. Name prefix encodes fabric type: `hsn*` → Slingshot (HPE Cray High-Speed Network); `ib*` → InfiniBand; `roce*` → RoCE. `lo` is filtered. |
| `fi_info -l` | List libfabric providers | libfabric is the transport abstraction layer used by Cray MPI and other HPC MPI implementations. `-l` lists available provider names without running any queries. Provider tokens: `cxi` (Slingshot), `verbs` (InfiniBand/RoCE RDMA verbs), `efa` (AWS EFA), `tcp`/`sockets` (software fallback). Missing `fi_info` → empty list, not an error. |
| `command -v ucx_info` | Detect UCX framework | UCX (Unified Communication X) is a separate transport framework from libfabric, used by OpenMPI and other runtimes on Linux InfiniBand/RoCE clusters. Binary presence on `PATH` → `provider:ucx` platform signal. Note: UCX and libfabric are independent stacks — a node can have one, both, or neither. |
| `ompi_info \| grep 'MCA pml'` | Detect active OpenMPI transport layer | OpenMPI's Point-to-Point Messaging Layer (PML) is configured at runtime. `MCA pml: ucx` means UCX is the active hardware transport. `ob1` and `cm` are software layers that OpenMPI always lists — they are filtered out because they are not hardware transports and would give a false impression of hardware capability. |

**How `communication_provider` is selected:**

UCX wins when a fast fabric (InfiniBand, RoCE, or Slingshot) is present, because UCX provides GPU-aware memory semantics via UCX UCM (CUDA/ROCm memory hooks). On Cray systems without UCX, CXI is the native Slingshot provider. The full fallback priority is: `ucx → cxi → verbs → efa → tcp → sockets`.

`available_providers` is the full ordered list of all detected transports (UCX first if present, then libfabric providers in detection order).

**Why `ob1` is filtered from `available_providers`:** `ob1` is OpenMPI's fallback software messaging layer. It can wrap any transport but does not represent a hardware path. Including it would imply hardware transport capability that may not exist.

---

### MPI detection (`probe_mpi`)

| Command | Why | What we extract |
|---------|-----|-----------------|
| `printf "OMPI_VERSION=%s\nMPICH_VERSION=%s\n" "$OMPI_VERSION" "$MPICH_VERSION"` | Read MPI version environment variables | Both OpenMPI and MPICH/Cray-MPICH set these in the shell when loaded via modules. `OMPI_VERSION` set → family `openmpi`; `MPICH_VERSION` set → family `mpich`. |
| `mpirun --version` | Fallback version detection | Used when env vars are empty. Parses the version banner for `open mpi` → `openmpi`; `mpich` or `hydra` (MPICH's process manager) → `mpich`. |

**MPI family** (`mpi.family`) feeds into `mpi_provider` in the hardware network section, the `context_name` derivation, and the `forbid_build` externals policy.

---

### Module system detection (`probe_modules`)

| Command | Why | What we extract |
|---------|-----|-----------------|
| `printf "LMOD_VERSION=%s\nMODULESHOME=%s\nMODULEPATH=%s\nLOADEDMODULES=%s\n"` | Read module environment in one shot | `LMOD_VERSION` set → `modules.system: lmod` (Lmod is the modern Lua-based module system used on most HPC sites); `MODULESHOME` set without `LMOD_VERSION` → `modules.system: tcl` (older Tcl/Environment Modules); `LOADEDMODULES` → colon-separated list of currently loaded modules; `MODULEPATH` → module search path. |

**How `context_name` is derived (in priority order):**

1. `prgenv_module` if set (Cray nodes): e.g. `PrgEnv-nvidia` — the Cray PE programming environment name is the most authoritative context identifier
2. The actual loaded module string from `LOADEDMODULES` that matches the MPI family: e.g. `openmpi/5.0` if `openmpi` is the detected MPI family — this preserves the full version string from the machine
3. The MPI family name as a fallback: e.g. `openmpi` — used when no loaded module matches

All three options come directly from the remote node. No context labels are hardcoded.

---

## Fabric command probes

The `clusterinspector fabric` command runs additional probes focused on network fabric health and classification. These run regardless of whether `--include-gpu` is set.

### Interface probe (`probe_interfaces`)

| Command | Why | What we extract |
|---------|-----|-----------------|
| `ip -o link show` | Interface state and MAC from the kernel | Parses one-line-per-interface output: name, link state (`UP`/`DOWN`/`UNKNOWN`), MAC address. |
| Sysfs dump (`/sys/class/net/*/operstate`, `address`, `device`) | Cross-reference with sysfs for device path | Links interface names to PCI device paths for driver correlation. Results are merged with `ip link show` output to get the most complete picture. |

### PCI probe (`probe_pci`)

| Command | Why | What we extract |
|---------|-----|-----------------|
| `lspci -mmD` or `/sys/bus/pci/devices/*/class` | Identify high-speed NIC PCI devices | PCI class code `0x0200` = Ethernet, `0x0207` = InfiniBand. Vendor/device IDs identify specific NIC families (Mellanox/NVIDIA, Cornelis, Cray CXI, etc.). |

### Driver probe (`probe_drivers`)

| Command | Why | What we extract |
|---------|-----|-----------------|
| `readlink /sys/class/net/<iface>/device/driver` | Identify loaded kernel driver for each interface | Driver name (e.g. `mlx5_core`, `irdma`, `cxi_core`) provides strong fabric-type evidence when interface naming is ambiguous. |

### RDMA probe (`probe_rdma`)

| Command | Why | What we extract |
|---------|-----|-----------------|
| `ls /sys/class/infiniband/` | Enumerate RDMA devices | RDMA subsystem entries confirm the kernel RDMA stack is loaded. Present for InfiniBand and RoCE; absent for Slingshot CXI (which uses its own subsystem). |
| `cat /sys/class/infiniband/*/ports/*/state` | Per-port RDMA link state | Values: `4: ACTIVE` = link up and passing traffic; `1: DOWN` / `2: INIT` = link is not active. A device present but no active ports → `rdma_link_inactive` diagnosis. |
| `rdma dev`, `rdma link`, `rdma resource` | RDMA device/link/resource inventory | Provides structured RDMA device metadata when the `rdma` utility is available. |

### libfabric probe (`probe_libfabric`)

| Command | Why | What we extract |
|---------|-----|-----------------|
| `fi_info -l` | List available libfabric providers | Quick provider enumeration. Used to confirm high-speed provider availability without running a full query. |
| `fi_info` | Full libfabric provider/interface detail | Shows which interfaces each provider is bound to, with address formats and capabilities. Used to correlate provider-to-interface relationships and confirm the fast path. |

### GPU hints probe (`probe_gpu_hints`, only with `--include-gpu`)

| Command | Why | What we extract |
|---------|-----|-----------------|
| `nvidia-smi topo -m` | GPU-NIC topology matrix | Same matrix as in the profile probe. Classifies network path as `possible_direct` (PIX/PXB/NV tokens between GPU and NIC) or `likely_host_staged` (SYS/SOC tokens). |
| `nvidia-smi --query-gpu=name --format=csv,noheader` | GPU count | Line count → `gpu_count` surfaced alongside the path classification. |
| `rocm-smi` | AMD GPU presence | Return code 0 with output → `gpu_vendor: amd`. |

GPU info (`gpu_vendor x gpu_count [path]`) appears in the per-node fabric output when `--include-gpu` is set, ensuring the fabric and profile commands agree on GPU presence.

---

## How health and diagnoses are derived (fabric command)

Evidence from all probe stages accumulates per node. Each piece of evidence has a code, message, source, and confidence level. The health classifier and diagnosis engine evaluate the combined evidence and assign:

- `health`: `healthy`, `degraded`, `warning`, or `unknown`
- `diagnoses`: a list of diagnosis codes (see `docs/fabric.md` for the full list)

Each diagnosis code maps to a human-readable message and an impact class. The evidence trail is available with `--evidence` so the reader can trace every conclusion back to the raw probe output that drove it.
