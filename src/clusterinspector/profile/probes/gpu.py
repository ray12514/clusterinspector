import re
from typing import Dict, List

from clusterinspector.core.runner import Runner


def _parse_nvidia_list(stdout: str) -> List[str]:
    return [line.strip() for line in (stdout or "").splitlines() if line.strip()]


def _parse_rocm_product_names(stdout: str) -> List[str]:
    models: List[str] = []
    for raw in (stdout or "").splitlines():
        line = raw.strip()
        if not line:
            continue
        lower = line.lower()
        if "card series:" in lower or "card model:" in lower:
            models.append(line.split(":", 1)[1].strip())
    return models


def _parse_nvidia_topology(stdout: str, gpu_count: int) -> Dict[str, object]:
    interconnect_type = ""
    interconnect_topology = ""
    gpu_nic_topology = ""
    numa_affinity: List[str] = []

    if gpu_count <= 0 or not (stdout or "").strip():
        return {
            "interconnect_type": interconnect_type,
            "interconnect_topology": interconnect_topology,
            "gpu_nic_topology": gpu_nic_topology,
            "numa_affinity": numa_affinity,
        }

    gpu_rows: List[List[str]] = []
    nic_rows: List[List[str]] = []
    for raw in stdout.splitlines():
        line = raw.strip()
        if not line or line.lower().startswith("legend"):
            continue
        parts = line.split()
        if not parts:
            continue
        label = parts[0]
        if re.fullmatch(r"GPU\d+", label):
            gpu_rows.append(parts)
        elif label.lower().startswith(("nic", "mlx", "ib", "hsn", "eth", "en")):
            nic_rows.append(parts)

    interconnect_tokens: List[str] = []
    for row_index, parts in enumerate(gpu_rows):
        links = parts[1 : 1 + gpu_count]
        for col_index, token in enumerate(links):
            if col_index != row_index and token != "X":
                interconnect_tokens.append(token)

        cpu_affinity = parts[1 + gpu_count] if len(parts) > 1 + gpu_count else ""
        numa_node = parts[2 + gpu_count] if len(parts) > 2 + gpu_count else ""
        if cpu_affinity or numa_node:
            summary = f"{parts[0]} -> cpu:{cpu_affinity or 'unknown'}"
            if numa_node:
                summary += f", numa:{numa_node}"
            numa_affinity.append(summary)

    if any(token.startswith("NV") for token in interconnect_tokens):
        interconnect_type = "nvlink"
        interconnect_topology = "nvlink_fabric"
    elif interconnect_tokens:
        interconnect_type = "pcie"
        interconnect_topology = "pcie"

    nic_summaries: List[str] = []
    for parts in nic_rows[:2]:
        links = parts[1 : 1 + gpu_count]
        gpu_links = [f"GPU{index}={token}" for index, token in enumerate(links) if token and token != "X"]
        if gpu_links:
            nic_summaries.append(f"{parts[0]}: {', '.join(gpu_links)}")
    if nic_summaries:
        gpu_nic_topology = "; ".join(nic_summaries)

    return {
        "interconnect_type": interconnect_type,
        "interconnect_topology": interconnect_topology,
        "gpu_nic_topology": gpu_nic_topology,
        "numa_affinity": numa_affinity,
    }


def _parse_amd_topology(stdout: str) -> Dict[str, object]:
    lines = [line.strip() for line in (stdout or "").splitlines() if line.strip()]
    lower = "\n".join(lines).lower()

    interconnect_type = ""
    interconnect_topology = ""
    if "xgmi" in lower:
        interconnect_type = "xgmi"
        interconnect_topology = "xgmi_fabric"
    elif "pcie" in lower:
        interconnect_type = "pcie"
        interconnect_topology = "pcie"

    numa_affinity = [line for line in lines if "numa" in line.lower()]
    gpu_nic_lines = [
        line
        for line in lines
        if "gpu" in line.lower() and any(token in line.lower() for token in ("nic", "hsn", "ib", "eth"))
    ]

    return {
        "interconnect_type": interconnect_type,
        "interconnect_topology": interconnect_topology,
        "gpu_nic_topology": "; ".join(gpu_nic_lines[:2]),
        "numa_affinity": numa_affinity,
    }


def probe_gpu(runner: Runner, host: str, timeout_s: int = 10) -> Dict[str, object]:
    nvidia_names = runner.run(
        host,
        ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
        timeout_s=timeout_s,
    )
    nvidia_cc = runner.run(
        host,
        ["nvidia-smi", "--query-gpu=compute_cap", "--format=csv,noheader"],
        timeout_s=timeout_s,
    )
    rocm_names = runner.run(
        host,
        ["bash", "-lc", "rocm-smi --showproductname 2>/dev/null"],
        timeout_s=timeout_s,
    )
    nvidia_topology = runner.run(
        host,
        ["bash", "-lc", "nvidia-smi topo -m 2>/dev/null"],
        timeout_s=timeout_s,
    )
    amd_topology = runner.run(
        host,
        ["bash", "-lc", "rocm-smi --showtopotype --showtoponuma 2>/dev/null"],
        timeout_s=timeout_s,
    )
    peer_mem = runner.run(
        host,
        ["bash", "-lc", "lsmod 2>/dev/null | grep -E 'nvidia_peermem|nv_peer_mem'"],
        timeout_s=timeout_s,
    )

    peer_mem_present = bool((peer_mem.stdout or "").strip())

    nvidia_models = _parse_nvidia_list(nvidia_names.stdout)
    if nvidia_models:
        cc_lines = _parse_nvidia_list(nvidia_cc.stdout)
        topology = _parse_nvidia_topology(nvidia_topology.stdout, len(nvidia_models))
        return {
            "vendor": "nvidia",
            "model": nvidia_models[0],
            "count_per_node": len(nvidia_models),
            "compute_capability": cc_lines[0] if cc_lines else "",
            "peer_mem_present": peer_mem_present,
            **topology,
        }

    amd_models = _parse_rocm_product_names(rocm_names.stdout)
    if amd_models:
        topology = _parse_amd_topology(amd_topology.stdout)
        return {
            "vendor": "amd",
            "model": amd_models[0],
            "count_per_node": len(amd_models),
            "compute_capability": "",
            "peer_mem_present": peer_mem_present,
            **topology,
        }

    return {
        "vendor": "unknown",
        "model": "",
        "count_per_node": 0,
        "compute_capability": "",
        "peer_mem_present": False,
        "interconnect_type": "",
        "interconnect_topology": "",
        "gpu_nic_topology": "",
        "numa_affinity": [],
    }
