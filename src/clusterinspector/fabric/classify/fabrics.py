from clusterinspector.core.confidence import from_agreement, from_signal_count
from clusterinspector.core.models import NodeReport


def _detect_from_driver(driver: str) -> str:
    d = (driver or "").lower()
    if d in {"mlx5_core", "mlx4_core"}:
        return "infiniband"
    if "cxi" in d:
        return "slingshot"
    if "hfi1" in d or "opa" in d:
        return "omnipath"
    if d:
        return "ethernet"
    return "unknown"


def classify_fabrics(node: NodeReport) -> NodeReport:
    labels = []
    for iface in node.interfaces:
        if iface.name == "lo":
            continue
        labels.append(_detect_from_driver(iface.driver))

    pci = node.raw.get("pci", {}) if isinstance(node.raw, dict) else {}
    families = pci.get("families", {}) if isinstance(pci, dict) else {}
    if families.get("hpe_slingshot"):
        labels.append("slingshot")
    if families.get("intel_opa"):
        labels.append("omnipath")
    if families.get("mellanox"):
        labels.append("infiniband")

    labels = [x for x in labels if x and x != "unknown"]
    unique = sorted(set(labels))
    if not unique:
        primary = "unknown"
        secondary = []
    elif len(unique) == 1:
        primary = unique[0]
        secondary = []
    else:
        primary = "mixed"
        secondary = unique

    node.primary_fabric = primary
    node.secondary_fabrics = secondary
    node.management_fabric = "ethernet"
    node.likely_hpc_fabric = unique[0] if unique else "unknown"
    node.health = "healthy" if unique else "unknown"
    node.confidence = from_agreement(labels)
    if node.confidence == "low":
        node.confidence = from_signal_count(len(node.evidence))

    if unique and all(x == "ethernet" for x in unique):
        node.diagnoses.append("tcp_fallback_likely")

    if families.get("mellanox") and not any(
        iface.driver in {"mlx5_core", "mlx4_core"} for iface in node.interfaces
    ):
        node.diagnoses.append("high_speed_nic_present_no_rdmastack")

    return node
