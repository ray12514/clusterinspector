from typing import Dict, Iterable, List


DIAGNOSIS_MESSAGES = {
    "tcp_fallback_likely": "Likely userspace fallback to TCP path",
    "high_speed_nic_present_no_rdmastack": "High-speed NIC detected without RDMA stack evidence",
    "rdma_link_inactive": "RDMA links were detected but none appear active",
    "possible_slingshot_path": "CXI/libfabric signals suggest a possible Slingshot path",
    "possible_roce_path": "Signals suggest a possible RoCE path",
    "node_unsuitable_for_multi_node_mpi": "Node likely unsuitable for multi-node MPI fast path",
    "fast_path_present_but_degraded": "Fast path is present but appears degraded",
    "gpu_network_path_likely_host_staged": "GPU traffic is likely host-staged",
    "node_probe_failed": "One or more probe stages failed on this node",
}


def diagnosis_message(code: str) -> str:
    return DIAGNOSIS_MESSAGES.get(code, code)


def diagnosis_details(codes: Iterable[str]) -> List[Dict[str, str]]:
    return [{"code": code, "message": diagnosis_message(code)} for code in codes]
