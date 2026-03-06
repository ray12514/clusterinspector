from clusterinspector.core.models import NodeReport


def classify_impact(node: NodeReport) -> NodeReport:
    libfabric = node.raw.get("libfabric", {}) if isinstance(node.raw, dict) else {}
    providers = set(libfabric.get("providers", [])) if isinstance(libfabric, dict) else set()

    if node.health == "impaired":
        if "node_unsuitable_for_multi_node_mpi" not in node.diagnoses:
            node.diagnoses.append("node_unsuitable_for_multi_node_mpi")

    if node.likely_hpc_fabric in {"infiniband", "roce", "slingshot", "omnipath"}:
        if not bool(libfabric.get("has_fast_provider")):
            if "tcp_fallback_likely" not in node.diagnoses:
                node.diagnoses.append("tcp_fallback_likely")

    if "cxi" in providers and "possible_slingshot_path" not in node.diagnoses:
        node.diagnoses.append("possible_slingshot_path")

    if node.likely_hpc_fabric == "roce" and "possible_roce_path" not in node.diagnoses:
        node.diagnoses.append("possible_roce_path")

    if node.health == "degraded" and "fast_path_present_but_degraded" not in node.diagnoses:
        node.diagnoses.append("fast_path_present_but_degraded")

    if node.gpu_network_path == "likely_host_staged":
        if "gpu_network_path_likely_host_staged" not in node.diagnoses:
            node.diagnoses.append("gpu_network_path_likely_host_staged")

    return node
