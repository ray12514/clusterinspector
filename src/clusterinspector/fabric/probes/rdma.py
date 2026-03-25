import re
from typing import Dict, List, Tuple

from clusterinspector.core.evidence import make_evidence
from clusterinspector.core.models import Evidence
from clusterinspector.core.runner import Runner
from clusterinspector.core.timeouts import Deadline


def _parse_sysfs_ib(stdout: str) -> List[str]:
    devices: List[str] = []
    for line in (stdout or "").splitlines():
        item = line.strip()
        if item and item != "(none)":
            devices.append(item)
    return devices


def _parse_sysfs_port_states(stdout: str) -> List[str]:
    return [line.strip() for line in (stdout or "").splitlines() if line.strip() and line.strip() != "(none)"]


def _line_has_active_state(line: str) -> bool:
    text = (line or "").strip().lower()
    if not text:
        return False

    if text.startswith("active"):
        return True
    if text.startswith("4: active"):
        return True

    patterns = [
        r"\bstate\b\s*(?:[:=]\s*)?(active|up)\b",
        r"\bport_state\b\s*(?:[:=]\s*)?(active|up)\b",
        r"\bphys_state\b\s*(?:[:=]\s*)?(active|up)\b",
    ]
    return any(re.search(pattern, text) for pattern in patterns)


def _active_count(lines: List[str]) -> int:
    count = 0
    for line in lines:
        if _line_has_active_state(line):
            count += 1
    return count


def probe_rdma(
    *,
    runner: Runner,
    host: str,
    deadline: Deadline,
    command_timeout_s: int,
) -> Tuple[Dict[str, object], List[Evidence]]:
    if deadline.expired():
        raise TimeoutError("node deadline expired before rdma probe")

    cmd_timeout = min(command_timeout_s, deadline.remaining_seconds())
    evidence: List[Evidence] = []

    sys_cmd = [
        "bash",
        "-lc",
        "ls -1 /sys/class/infiniband 2>/dev/null || printf '(none)\\n'",
    ]
    sys_res = runner.run(host, sys_cmd, timeout_s=cmd_timeout)
    ib_devices = _parse_sysfs_ib(sys_res.stdout)

    port_state_cmd = [
        "bash",
        "-lc",
        "for p in /sys/class/infiniband/*/ports/*/state; do [ -r \"$p\" ] || continue; cat \"$p\" 2>/dev/null; done",
    ]
    port_state_res = runner.run(host, port_state_cmd, timeout_s=cmd_timeout)
    port_state_lines = _parse_sysfs_port_states(port_state_res.stdout)

    rdma_dev = runner.run(host, ["rdma", "dev", "show"], timeout_s=cmd_timeout)
    rdma_link = runner.run(host, ["rdma", "link", "show"], timeout_s=cmd_timeout)
    rdma_resource = runner.run(host, ["rdma", "resource", "show"], timeout_s=cmd_timeout)

    dev_lines = [ln.strip() for ln in (rdma_dev.stdout or "").splitlines() if ln.strip()]
    link_lines = [ln.strip() for ln in (rdma_link.stdout or "").splitlines() if ln.strip()]
    resource_lines = [ln.strip() for ln in (rdma_resource.stdout or "").splitlines() if ln.strip()]
    rdma_link_count = max(len(link_lines), len(port_state_lines))

    active_links = max(_active_count(link_lines), _active_count(port_state_lines))
    has_rdma_stack = bool(ib_devices or dev_lines or link_lines or port_state_lines)

    if has_rdma_stack:
        evidence.append(
            make_evidence(
                code="rdma_stack_visible",
                message="RDMA stack signals are visible",
                source="rdma",
                confidence="high",
                data={
                    "ib_devices": len(ib_devices),
                    "rdma_dev_lines": len(dev_lines),
                    "rdma_link_lines": len(link_lines),
                    "sysfs_port_states": len(port_state_lines),
                },
            )
        )
    else:
        evidence.append(
            make_evidence(
                code="rdma_stack_not_visible",
                message="No RDMA stack signal found from sysfs or rdma CLI",
                source="rdma",
                confidence="medium",
            )
        )

    if rdma_link_count > 0:
        if active_links > 0:
            evidence.append(
                make_evidence(
                    code="rdma_link_active",
                    message=f"Detected {active_links} active RDMA links",
                    source="rdma",
                    confidence="high",
                )
            )
        else:
            evidence.append(
                make_evidence(
                    code="rdma_link_no_active",
                    message="RDMA links exist but none are active",
                    source="rdma",
                    confidence="high",
                )
            )

    if rdma_dev.returncode not in (0, 127):
        evidence.append(
            make_evidence(
                code="rdma_cli_error",
                message="rdma dev show failed",
                source="rdma",
                confidence="medium",
                data={"stderr": rdma_dev.stderr.strip()},
            )
        )
    if rdma_link.returncode not in (0, 127):
        evidence.append(
            make_evidence(
                code="rdma_cli_error",
                message="rdma link show failed",
                source="rdma",
                confidence="medium",
                data={"stderr": rdma_link.stderr.strip()},
            )
        )
    if rdma_resource.returncode not in (0, 127):
        evidence.append(
            make_evidence(
                code="rdma_cli_error",
                message="rdma resource show failed",
                source="rdma",
                confidence="low",
                data={"stderr": rdma_resource.stderr.strip()},
            )
        )

    return {
        "sysfs_infiniband": ib_devices,
        "sysfs_port_state_lines": port_state_lines,
        "rdma_dev_lines": dev_lines,
        "rdma_link_lines": link_lines,
        "rdma_resource_lines": resource_lines,
        "sysfs_count": len(ib_devices),
        "rdma_device_count": len(dev_lines),
        "rdma_link_count": rdma_link_count,
        "active_link_count": active_links,
        "has_rdma_stack": has_rdma_stack,
    }, evidence
