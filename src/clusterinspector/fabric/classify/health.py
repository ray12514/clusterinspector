from clusterinspector.core.models import NodeReport


def classify_health(node: NodeReport) -> NodeReport:
    rdma = node.raw.get("rdma", {}) if isinstance(node.raw, dict) else {}
    libfabric = node.raw.get("libfabric", {}) if isinstance(node.raw, dict) else {}

    hpc = (node.likely_hpc_fabric or "unknown").lower()
    has_rdma = bool(rdma.get("has_rdma_stack"))
    rdma_link_count = int(rdma.get("rdma_link_count", 0) or 0)
    active_links = int(rdma.get("active_link_count", 0) or 0)
    has_fast_provider = bool(libfabric.get("has_fast_provider"))

    if hpc in {"unknown", "ethernet"}:
        node.health = "healthy" if hpc == "ethernet" else "unknown"
        return node

    if rdma_link_count > 0 and active_links == 0:
        node.health = "impaired"
        if "rdma_link_inactive" not in node.diagnoses:
            node.diagnoses.append("rdma_link_inactive")
        return node

    if has_rdma and has_fast_provider:
        node.health = "healthy"
        return node

    if has_rdma or has_fast_provider:
        node.health = "degraded"
        return node

    node.health = "impaired"
    return node
