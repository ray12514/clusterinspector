from typing import Dict, List

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


def _primary_fabric(nics: List[Dict[str, str]]) -> str:
    fabrics = [nic.get("fabric", "unknown") for nic in nics if nic.get("fabric")]
    unique = sorted({fabric for fabric in fabrics if fabric and fabric != "unknown"})
    if not unique:
        return "unknown"
    if len(unique) == 1:
        return unique[0]
    return "mixed"


def _primary_provider(providers: List[str]) -> str:
    for candidate in ("cxi", "verbs", "efa", "tcp", "sockets"):
        if candidate in providers:
            return candidate
    return providers[0] if providers else "unknown"


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

    names = _parse_interfaces(interfaces.stdout)
    provider_tokens = _parse_providers(providers.stdout)
    nics = [{"name": name, "fabric": _infer_fabric(name, provider_tokens)} for name in names]

    return {
        "nics": nics,
        "providers": provider_tokens,
        "network": {
            "fabric": _primary_fabric(nics),
            "communication_provider": _primary_provider(provider_tokens),
        },
    }
