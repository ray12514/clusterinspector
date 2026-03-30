import re
from typing import Dict, List, Tuple

from clusterinspector.core.evidence import make_evidence
from clusterinspector.core.models import Evidence
from clusterinspector.core.runner import Runner
from clusterinspector.core.timeouts import Deadline


def _contains_direct_tokens(lines: List[str]) -> bool:
    text = "\n".join(lines).lower()
    return any(tok in text for tok in ("pix", "pxb", "nv", "xgmi", "gpudirect"))


def _contains_staged_tokens(lines: List[str]) -> bool:
    text = "\n".join(lines).lower()
    return any(tok in text for tok in ("sys", "soc", "host bridge"))


def probe_gpu_hints(
    *,
    runner: Runner,
    host: str,
    deadline: Deadline,
    command_timeout_s: int,
) -> Tuple[Dict[str, object], List[Evidence]]:
    if deadline.expired():
        raise TimeoutError("node deadline expired before gpu probe")

    cmd_timeout = min(command_timeout_s, deadline.remaining_seconds())
    evidence: List[Evidence] = []

    nvidia = runner.run(host, ["nvidia-smi", "topo", "-m"], timeout_s=cmd_timeout)
    nvidia_names = runner.run(
        host,
        ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
        timeout_s=cmd_timeout,
    )
    rocm = runner.run(host, ["rocm-smi"], timeout_s=cmd_timeout)

    nvidia_lines = [ln.strip() for ln in (nvidia.stdout or "").splitlines() if ln.strip()]
    rocm_lines = [ln.strip() for ln in (rocm.stdout or "").splitlines() if ln.strip()]

    gpu_vendor = "unknown"
    gpu_count = 0
    if nvidia.returncode == 0 and nvidia_lines:
        gpu_vendor = "nvidia"
        gpu_count = sum(1 for ln in (nvidia_names.stdout or "").splitlines() if ln.strip())
    elif rocm.returncode == 0 and rocm_lines:
        gpu_vendor = "amd"
        gpu_count = sum(1 for ln in rocm_lines if "card series:" in ln.lower())

    path_label = "unknown"
    combined = nvidia_lines + rocm_lines
    if _contains_direct_tokens(combined):
        path_label = "possible_direct"
    elif _contains_staged_tokens(combined):
        path_label = "likely_host_staged"

    if gpu_vendor != "unknown":
        evidence.append(
            make_evidence(
                code="gpu_tooling_visible",
                message=f"Detected GPU tooling for {gpu_vendor} x{gpu_count}",
                source="gpu",
                confidence="medium",
            )
        )

    if path_label != "unknown":
        evidence.append(
            make_evidence(
                code=f"gpu_path_{path_label}",
                message=f"GPU-network path hint: {path_label}",
                source="gpu",
                confidence="low",
            )
        )

    if nvidia.returncode == 127 and rocm.returncode == 127:
        evidence.append(
            make_evidence(
                code="gpu_tooling_unavailable",
                message="GPU tooling not available (nvidia-smi/rocm-smi)",
                source="gpu",
                confidence="low",
            )
        )

    return {
        "gpu_vendor": gpu_vendor,
        "gpu_count": gpu_count,
        "gpu_network_path": path_label,
        "nvidia_topology_lines": nvidia_lines,
        "rocm_lines": rocm_lines,
        "nvidia_returncode": nvidia.returncode,
        "rocm_returncode": rocm.returncode,
    }, evidence
