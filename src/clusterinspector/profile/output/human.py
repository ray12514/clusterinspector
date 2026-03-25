from typing import Dict, List


def _render_profile(profile: Dict[str, object]) -> List[str]:
    system = profile.get("system", {})
    hardware = profile.get("hardware", {})
    gpus = hardware.get("gpus", {})
    network = hardware.get("network", {})
    modules = profile.get("modules", {})
    active_context = modules.get("active_context", {})
    vendor_substrate = profile.get("vendor_substrate", {})
    scheduler = profile.get("scheduler", {})
    capabilities = profile.get("capabilities", {})

    lines = [
        f"Profile: {system.get('name', 'unknown')}",
        f"  Platform class: {system.get('platform_class', 'unknown')}",
        f"  Node role: {system.get('node_role', 'unknown')}",
        f"  Environment model: {system.get('environment_model', 'unknown')}",
        f"  Classification confidence: {system.get('classification_confidence', 'low')}",
        f"  Site: {system.get('site', 'unknown')}",
        f"  Scheduler: {scheduler.get('type', 'unknown')}",
        f"  GPU: {gpus.get('vendor', 'unknown')} {gpus.get('model', '')} x{gpus.get('count_per_node', 0)}".rstrip(),
        f"  GPU interconnect: {gpus.get('interconnect_type', '') or 'unknown'}",
        f"  Network fabric: {network.get('fabric', 'unknown')}",
        f"  Communication provider: {network.get('communication_provider', 'unknown')}",
        f"  Active context: {active_context.get('prgenv_module', '') or active_context.get('mpi_module', '') or 'default shell'}",
        f"  Context name: {active_context.get('context_name', '') or 'unspecified'}",
        f"  Wrapper family: {active_context.get('compiler_wrapper_family', 'unknown')}",
        f"  Compiler wrappers: {', '.join(vendor_substrate.get('compiler_wrappers', [])) or 'unknown'}",
        f"  Signals: {', '.join(system.get('observed_platform_signals', [])) or 'none'}",
        "  Capabilities:",
        f"    T0: {capabilities.get('t0', {}).get('state', 'unknown')}",
        f"    T1: {capabilities.get('t1', {}).get('state', 'unknown')}",
        f"    T2: {capabilities.get('t2', {}).get('state', 'unknown')}",
        f"    T3: {capabilities.get('t3', {}).get('state', 'unknown')}",
    ]
    return lines


def render_human(profile: dict) -> str:
    if "profiles" in profile:
        lines = ["Profiles:"]
        for item in profile["profiles"]:
            lines.extend(_render_profile(item))
        return "\n".join(lines)
    return "\n".join(_render_profile(profile))
