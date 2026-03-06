from typing import Dict, List, Tuple

from clusterinspector.core.evidence import make_evidence
from clusterinspector.core.models import Evidence
from clusterinspector.core.runner import Runner
from clusterinspector.core.timeouts import Deadline


def _detect_families(lines: List[str]) -> Dict[str, bool]:
    txt = "\n".join(lines).lower()
    return {
        "mellanox": ("mellanox" in txt) or ("mlx" in txt),
        "hpe_slingshot": ("cxi" in txt) or ("cassini" in txt) or ("hpe" in txt and "slingshot" in txt),
        "intel_opa": ("omni-path" in txt) or ("omnipath" in txt),
        "broadcom": "broadcom" in txt,
    }


def probe_pci(
    *,
    runner: Runner,
    host: str,
    deadline: Deadline,
    command_timeout_s: int,
) -> Tuple[Dict[str, object], List[Evidence]]:
    if deadline.expired():
        raise TimeoutError("node deadline expired before pci probe")

    cmd_timeout = min(command_timeout_s, deadline.remaining_seconds())
    res = runner.run(host, ["lspci", "-nn"], timeout_s=cmd_timeout)
    lines = [ln for ln in (res.stdout or "").splitlines() if ln.strip()]
    nic_lines = [ln for ln in lines if any(k in ln.lower() for k in ("ethernet", "infiniband", "network"))]
    families = _detect_families(nic_lines)

    ev: List[Evidence] = []
    if res.returncode == 0:
        ev.append(
            make_evidence(
                code="pci_inventory_collected",
                message=f"Collected {len(nic_lines)} NIC-related PCI records",
                source="pci",
                confidence="medium",
            )
        )
    else:
        ev.append(
            make_evidence(
                code="lspci_unavailable",
                message="lspci command unavailable or failed",
                source="pci",
                confidence="medium",
                data={"stderr": res.stderr.strip()},
            )
        )

    for family, present in families.items():
        if present:
            ev.append(
                make_evidence(
                    code=f"pci_family_{family}",
                    message=f"Detected {family} PCI signature",
                    source="pci",
                    confidence="medium",
                )
            )

    return {
        "returncode": res.returncode,
        "nic_lines": nic_lines,
        "families": families,
    }, ev
