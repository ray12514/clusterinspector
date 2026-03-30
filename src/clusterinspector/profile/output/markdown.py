from typing import List


def _render_profile(profile: dict) -> List[str]:
    system = profile.get("system", {})
    hardware = profile.get("hardware", {})
    gpus = hardware.get("gpus", {})
    network = hardware.get("network", {})
    modules = profile.get("modules", {})
    active_context = modules.get("active_context", {})
    scheduler = profile.get("scheduler", {})
    capabilities = profile.get("capabilities", {})
    vendor_substrate = profile.get("vendor_substrate", {})

    _comm = network.get("communication_provider", "unknown")
    _avail = network.get("available_providers", [])
    _avail_str = f" (available: {', '.join(_avail)})" if len(_avail) > 1 else ""

    return [
        f"# Profile: {system.get('name', 'unknown')}",
        "",
        "## System",
        f"- **Platform class:** {system.get('platform_class', 'unknown')}",
        f"- **Node role:** {system.get('node_role', 'unknown')}",
        f"- **Environment model:** {system.get('environment_model', 'unknown')}",
        f"- **Classification confidence:** {system.get('classification_confidence', 'low')}",
        f"- **Site:** {system.get('site', 'unknown')}",
        f"- **Scheduler:** {scheduler.get('type', 'unknown')}",
        f"- **Signals:** {', '.join(system.get('observed_platform_signals', [])) or 'none'}",
        "",
        "## Hardware",
        f"- **GPU:** {gpus.get('vendor', 'unknown')} {gpus.get('model', '')} x{gpus.get('count_per_node', 0)}".rstrip(),
        f"- **GPU interconnect:** {gpus.get('interconnect_type', '') or 'unknown'}",
        f"- **Network fabric:** {network.get('fabric', 'unknown')}",
        f"- **Communication provider:** {_comm}{_avail_str}",
        f"- **MPI provider:** {network.get('mpi_provider', 'unknown')}",
        "",
        "## Active Context",
        f"- **Context:** {active_context.get('context_name', '') or 'unspecified'}",
        f"- **Wrapper family:** {active_context.get('compiler_wrapper_family', 'unknown')}",
        f"- **Compiler wrappers:** {', '.join(vendor_substrate.get('compiler_wrappers', [])) or 'unknown'}",
        "",
        "## Capabilities",
        f"- **T0:** {capabilities.get('t0', {}).get('state', 'unknown')}",
        f"- **T1:** {capabilities.get('t1', {}).get('state', 'unknown')}",
        f"- **T2:** {capabilities.get('t2', {}).get('state', 'unknown')}",
        f"- **T3:** {capabilities.get('t3', {}).get('state', 'unknown')}",
        f"- **MPI GPU-aware:** {capabilities.get('mpi_gpu_aware', {}).get('state', 'unknown')}",
        f"- **GPUDirect RDMA:** {capabilities.get('gpudirect_rdma', {}).get('state', 'unknown')}",
    ]


def render_markdown(profile: dict) -> str:
    if "profiles" in profile:
        sections: List[str] = []
        for item in profile["profiles"]:
            sections.append("\n".join(_render_profile(item)))
        return "\n\n---\n\n".join(sections)
    return "\n".join(_render_profile(profile))
