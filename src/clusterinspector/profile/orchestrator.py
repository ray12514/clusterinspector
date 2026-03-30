from typing import Dict, List, Optional

from clusterinspector.core.host_resolver import resolve_hosts
from clusterinspector.core.local import LocalRunner
from clusterinspector.core.runner import Runner
from clusterinspector.core.ssh import SSHRunner
from clusterinspector.profile.probes.compiler import probe_compiler
from clusterinspector.profile.probes.fabric import probe_fabric_hints
from clusterinspector.profile.probes.gpu import probe_gpu
from clusterinspector.profile.probes.modules import probe_modules
from clusterinspector.profile.probes.mpi import probe_mpi
from clusterinspector.profile.probes.system import probe_system
from clusterinspector.profile.schema import capability_state, empty_profile, wrap_profiles


def _platform_class(*, gpu_vendor: str, is_cray: bool) -> str:
    if gpu_vendor == "nvidia":
        return "cray-nvidia" if is_cray else "linux-nvidia"
    if gpu_vendor == "amd":
        return "cray-amd" if is_cray else "linux-amd"
    return "unknown"


def _forbid_builds(platform_class: str, gpu_vendor: str, mpi_module: str) -> List[str]:
    forbidden: List[str] = []
    if platform_class.startswith("cray") and mpi_module:
        forbidden.append(mpi_module)
    if gpu_vendor == "nvidia":
        forbidden.append("cuda")
    elif gpu_vendor == "amd":
        forbidden.append("rocm")
    return forbidden


def _wrapper_family(wrappers: List[str]) -> str:
    wrapper_set = set(wrappers)
    if {"cc", "CC", "ftn"}.issubset(wrapper_set):
        return "cray_wrappers"
    if {"mpicc", "mpicxx", "mpifort"}.issubset(wrapper_set):
        return "direct_mpi_wrappers"
    if wrappers:
        return "other"
    return "unknown"


def _environment_model(*, is_cray: bool, wrapper_family: str, modules_system: str) -> str:
    if is_cray:
        return "cray_pe"
    if wrapper_family == "direct_mpi_wrappers":
        return "direct_mpi"
    if modules_system in {"lmod", "tcl"}:
        return "module_driven"
    return "unknown"


def _node_role(*, gpu_count: int, scheduler_type: str) -> str:
    if gpu_count > 0:
        return "gpu_compute"
    if scheduler_type in {"slurm", "pbs"}:
        return "cpu_compute"
    return "login_or_service"


def _observed_platform_signals(
    *,
    gpu_vendor: str,
    is_cray: bool,
    wrapper_family: str,
    modules_system: str,
    mpi_family: str,
    providers: List[str],
    available_providers: List[str],
    nics: List[Dict[str, str]],
) -> List[str]:
    signals: List[str] = []
    if is_cray:
        signals.append("cray_pe")
    if gpu_vendor != "unknown":
        signals.append(f"gpu_vendor:{gpu_vendor}")
    if wrapper_family != "unknown":
        signals.append(f"wrapper_family:{wrapper_family}")
    if modules_system != "unknown":
        signals.append(f"modules:{modules_system}")
    if mpi_family != "unknown":
        signals.append(f"mpi:{mpi_family}")
    if "cxi" in providers:
        signals.append("provider:cxi")
    if "verbs" in providers:
        signals.append("provider:verbs")
    if "ucx" in available_providers:
        signals.append("provider:ucx")
    if any(nic.get("fabric") == "slingshot" for nic in nics):
        signals.append("fabric:slingshot")
    if any(nic.get("fabric") == "infiniband" for nic in nics):
        signals.append("fabric:infiniband")
    if any(nic.get("fabric") == "roce" for nic in nics):
        signals.append("fabric:roce")
    return signals


def _classification_confidence(*, platform_class: str, gpu_vendor: str, wrapper_family: str, is_cray: bool) -> str:
    if platform_class != "unknown" and gpu_vendor != "unknown" and wrapper_family != "unknown":
        return "high"
    if is_cray or gpu_vendor != "unknown" or wrapper_family != "unknown":
        return "medium"
    return "low"


def _has_fast_fabric(nics: List[Dict[str, str]]) -> bool:
    return any(nic.get("fabric") in {"slingshot", "infiniband", "roce"} for nic in nics)


def _apply_capabilities(
    profile: Dict[str, object],
    mpi_family: str,
    available_providers: List[str],
    gpu: Dict[str, object],
    compiler: Dict[str, object],
) -> None:
    capabilities = profile["capabilities"]
    gpus = profile["hardware"]["gpus"]
    nics = profile["hardware"]["nics"]

    has_gpu = gpus.get("count_per_node", 0) > 0
    has_mpi = mpi_family != "unknown"
    has_fast_fabric = _has_fast_fabric(nics)
    # UCX (Linux/OpenMPI path) and CXI (Cray/Slingshot via GTL) are both GPU-aware transports
    has_gpu_transport = has_fast_fabric and (
        "ucx" in available_providers or "cxi" in available_providers
    )

    # GPUDirect RDMA requires kernel peer-memory support OR Cray CXI GTL.
    # Fast fabric + GPU alone is not sufficient — e.g. LIQID PCIe-switched systems
    # route GPU↔NIC traffic through host memory (SYS/SOC topology tokens).
    peer_mem = bool(gpu.get("peer_mem_present", False))
    # Cray GTL (GPU Transport Layer) provides GPU RDMA over Slingshot CXI natively
    has_cxi_gtl = "cxi" in available_providers and bool(compiler.get("is_cray", False))
    has_gpu_rdma_evidence = peer_mem or has_cxi_gtl
    # Topology hint: PIX/PXB = same/nearby PCIe root (structurally possible); SYS/SOC = host-staged
    gpu_nic_topo = str(gpu.get("gpu_nic_topology", "")).upper()
    has_direct_path = any(t in gpu_nic_topo for t in ("PIX", "PXB", "NV"))

    capabilities["t0"] = capability_state("observed" if has_gpu else "unknown")
    capabilities["t1"] = capability_state("inferred" if has_gpu and has_mpi else "unknown")
    capabilities["t2"] = capability_state("observed" if has_gpu and has_fast_fabric else "unknown")
    capabilities["t3"] = capability_state("unknown")
    capabilities["mpi_gpu_aware"] = capability_state(
        "observed" if has_gpu and has_mpi and has_gpu_transport
        else "inferred" if has_gpu and has_mpi
        else "unknown"
    )
    capabilities["gpudirect_rdma"] = capability_state(
        "observed" if has_gpu and has_fast_fabric and has_gpu_rdma_evidence
        else "inferred" if has_gpu and has_fast_fabric and has_direct_path
        else "unknown"
    )
    capabilities["dl_collectives"] = capability_state("unknown")


def _profile_host(runner: Runner, host: str) -> Dict[str, object]:
    system = probe_system(runner, host)
    gpu = probe_gpu(runner, host)
    compiler = probe_compiler(runner, host)
    modules = probe_modules(runner, host)
    mpi = probe_mpi(runner, host)
    fabric = probe_fabric_hints(runner, host)

    hostname = str(system["hostname"])
    profile = empty_profile(hostname)

    platform_class = _platform_class(gpu_vendor=str(gpu["vendor"]), is_cray=bool(compiler["is_cray"]))
    loaded_modules = modules.get("loaded", [])
    cuda_module = next((item for item in loaded_modules if "cuda" in item.lower()), "")
    rocm_module = next((item for item in loaded_modules if "rocm" in item.lower()), "")
    mpi_module = str(mpi.get("module_name") or "")
    wrapper_family = _wrapper_family(list(compiler["compiler_wrappers"]))
    environment_model = _environment_model(
        is_cray=bool(compiler["is_cray"]),
        wrapper_family=wrapper_family,
        modules_system=str(modules["system"]),
    )
    node_role = _node_role(
        gpu_count=int(gpu.get("count_per_node", 0) or 0),
        scheduler_type=str(system["scheduler"]["type"]),
    )
    available_providers = list(fabric.get("available_providers", []))
    observed_signals = _observed_platform_signals(
        gpu_vendor=str(gpu["vendor"]),
        is_cray=bool(compiler["is_cray"]),
        wrapper_family=wrapper_family,
        modules_system=str(modules["system"]),
        mpi_family=str(mpi["family"]),
        providers=list(fabric["providers"]),
        available_providers=available_providers,
        nics=list(fabric["nics"]),
    )
    classification_confidence = _classification_confidence(
        platform_class=platform_class,
        gpu_vendor=str(gpu["vendor"]),
        wrapper_family=wrapper_family,
        is_cray=bool(compiler["is_cray"]),
    )

    profile["system"] = {
        "name": hostname,
        "site": system["site"],
        "platform_class": platform_class,
        "node_role": node_role,
        "environment_model": environment_model,
        "observed_platform_signals": observed_signals,
        "classification_confidence": classification_confidence,
    }
    profile["os"] = system["os"]
    profile["modules"] = {
        "system": modules["system"],
        "modulepath": modules["modulepath"],
        "hierarchy_notes": modules["hierarchy_notes"],
        "loaded": loaded_modules,
        "active_context": {
            "source": "active_shell",
            "context_name": str(compiler["prgenv_module"] or next(
                (m for m in loaded_modules if str(mpi["family"]) and str(mpi["family"]) in m.lower()),
                mpi["family"],
            ) or ""),
            "prgenv_module": compiler["prgenv_module"],
            "gpu_runtime_module": cuda_module or rocm_module,
            "mpi_module": mpi_module,
            "compiler_wrapper_family": wrapper_family,
        },
    }
    profile["scheduler"] = system["scheduler"]
    profile["hardware"] = {
        "cpu": system["cpu"],
        "gpus": gpu,
        "nics": fabric["nics"],
        "network": {
            "fabric": fabric.get("network", {}).get("fabric", "unknown"),
            "communication_provider": fabric.get("network", {}).get("communication_provider", "unknown"),
            "available_providers": available_providers,
            "mpi_provider": str(mpi["family"]),
        },
    }
    profile["vendor_substrate"] = {
        "prgenv_module": compiler["prgenv_module"],
        "compiler_wrappers": compiler["compiler_wrappers"],
        "mpi_module": mpi_module,
        "mpi_family": str(mpi["family"]),
        "cuda_module": cuda_module,
        "rocm_module": rocm_module,
        "source": "active_environment" if loaded_modules else "command_detection",
    }
    profile["externals_policy"] = {
        "forbid_build": _forbid_builds(platform_class, str(gpu["vendor"]), mpi_module),
        "module_based_externals": bool(loaded_modules or compiler["prgenv_module"]),
    }
    profile["validation_evidence"] = {
        "last_validated": "",
        "validation_layers": [],
        "tests_run": [],
    }

    _apply_capabilities(profile, str(mpi["family"]), available_providers, gpu, compiler)
    return profile


def collect_profiles(args, runner: Optional[Runner] = None) -> List[Dict[str, object]]:
    hosts = resolve_hosts(
        local=bool(args.local),
        nodes=args.nodes or None,
        hosts_file=None,
        scheduler=None,
    )
    if not hosts:
        raise ValueError("no hosts resolved; use --local or --nodes")

    active_runner = runner
    if active_runner is None:
        active_runner = LocalRunner() if args.local else SSHRunner()

    return [_profile_host(active_runner, host) for host in hosts]


def collect_profile(args, runner: Optional[Runner] = None) -> Dict[str, object]:
    return wrap_profiles(collect_profiles(args, runner=runner))
