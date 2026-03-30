from typing import Dict, List, Tuple

from clusterinspector.core.runner import Runner


def _infer_fabric(interface_name: str, providers: List[str]) -> str:
    name = (interface_name or "").lower()
    if name.startswith("hsn") or "cxi" in providers:
        return "slingshot"
    if name.startswith("ib") or "verbs" in providers:
        return "infiniband"
    if name.startswith("roce"):
        return "roce"
    return "ethernet"


def _parse_interfaces(stdout: str) -> List[str]:
    return [line.strip() for line in (stdout or "").splitlines() if line.strip() and line.strip() != "lo"]


def _parse_providers(stdout: str) -> List[str]:
    providers: List[str] = []
    for raw in (stdout or "").splitlines():
        token = raw.strip().split(None, 1)[0].strip(":").lower()
        if token and token not in providers:
            providers.append(token)
    return providers


def _parse_ompi_pmls(stdout: str) -> List[str]:
    """Parse 'ompi_info | grep MCA pml' output → hardware transport PML names only.

    Sample input:
        "                 MCA pml: ucx (MCA v2.1.0, API v2.0.0, Component v5.0.6)"
        "                 MCA pml: ob1 (MCA v2.1.0, API v2.0.0, Component v5.0.6)"
    Sample output:
        ["ucx"]   (ob1/cm are software layers, not hardware transports — filtered out)
    """
    _TRANSPORT_PMLS = {"ucx"}
    pmls: List[str] = []
    for raw in (stdout or "").splitlines():
        if "MCA pml:" not in raw:
            continue
        _, _, rhs = raw.partition("MCA pml:")
        token = rhs.strip().split(None, 1)[0].lower()
        if token in _TRANSPORT_PMLS and token not in pmls:
            pmls.append(token)
    return pmls


def _build_available_providers(
    libfabric: List[str], ucx_present: bool, ompi_pmls: List[str]
) -> List[str]:
    """Merge all detected transport sources into an ordered list.

    UCX comes first (highest GPU workload priority), then libfabric providers in
    their natural order. ob1/cm ompi_pmls entries are excluded — they are MPI
    software layers, not hardware transports.
    """
    available: List[str] = []
    if ucx_present or "ucx" in ompi_pmls:
        available.append("ucx")
    for p in libfabric:
        if p not in available:
            available.append(p)
    return available


def _has_fast_fabric_from_nics(nics: List[Dict[str, str]]) -> bool:
    return any(nic.get("fabric") in {"slingshot", "infiniband", "roce"} for nic in nics)


def _primary_fabric(nics: List[Dict[str, str]]) -> str:
    fabrics = [nic.get("fabric", "unknown") for nic in nics if nic.get("fabric")]
    unique = sorted({fabric for fabric in fabrics if fabric and fabric != "unknown"})
    if not unique:
        return "unknown"
    if len(unique) == 1:
        return unique[0]
    return "mixed"


def _optimal_provider(available: List[str], has_fast_fabric: bool) -> str:
    """Select the optimal communication provider for GPU workloads.

    UCX is preferred when fast fabric (IB/RoCE/Slingshot) is present because it
    provides GPU-aware memory semantics (CUDA/ROCm via UCM). CXI is the native
    Slingshot provider and wins when UCX is absent.
    """
    if has_fast_fabric and "ucx" in available:
        return "ucx"
    for candidate in ("cxi", "verbs", "efa", "ucx", "tcp", "sockets"):
        if candidate in available:
            return candidate
    return available[0] if available else "unknown"


def probe_fabric_hints(runner: Runner, host: str, timeout_s: int = 10) -> Dict[str, object]:
    interfaces = runner.run(
        host,
        ["bash", "-lc", 'for n in /sys/class/net/*; do [ -e "$n" ] || continue; basename "$n"; done 2>/dev/null | sort'],
        timeout_s=timeout_s,
    )
    providers = runner.run(
        host,
        ["bash", "-lc", "fi_info -l 2>/dev/null"],
        timeout_s=timeout_s,
    )
    ucx_check = runner.run(
        host,
        ["bash", "-lc", "command -v ucx_info >/dev/null 2>&1 && echo ucx_present"],
        timeout_s=timeout_s,
    )
    ompi_pml_out = runner.run(
        host,
        ["bash", "-lc", "ompi_info 2>/dev/null | grep 'MCA pml'"],
        timeout_s=timeout_s,
    )

    names = _parse_interfaces(interfaces.stdout)
    provider_tokens = _parse_providers(providers.stdout)
    nics = [{"name": name, "fabric": _infer_fabric(name, provider_tokens)} for name in names]

    ucx_present = "ucx_present" in (ucx_check.stdout or "")
    ompi_pmls = _parse_ompi_pmls(ompi_pml_out.stdout)
    available = _build_available_providers(provider_tokens, ucx_present, ompi_pmls)
    fast_fabric = _has_fast_fabric_from_nics(nics)

    return {
        "nics": nics,
        "providers": provider_tokens,
        "available_providers": available,
        "network": {
            "fabric": _primary_fabric(nics),
            "communication_provider": _optimal_provider(available, fast_fabric),
        },
    }
