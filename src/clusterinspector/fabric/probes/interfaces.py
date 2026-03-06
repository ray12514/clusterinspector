import re
from typing import Dict, List, Tuple

from clusterinspector.core.evidence import make_evidence
from clusterinspector.core.models import Evidence, InterfaceRecord
from clusterinspector.core.runner import Runner
from clusterinspector.core.timeouts import Deadline


def _parse_ip_link(stdout: str) -> Dict[str, Dict[str, str]]:
    by_iface: Dict[str, Dict[str, str]] = {}
    for line in (stdout or "").splitlines():
        match = re.match(r"^\d+:\s+([^:]+):\s+(.*)$", line.strip())
        if not match:
            continue
        ifname = match.group(1)
        right = match.group(2)
        name = ifname.strip().split("@", 1)[0]
        if "link/" not in right:
            continue
        state = "unknown"
        if "state " in right:
            state = right.split("state ", 1)[1].split(" ", 1)[0].strip().lower()
        mac = right.split("link/", 1)[1].split()
        by_iface[name] = {
            "operstate": state,
            "mac": mac[1] if len(mac) > 1 else "",
        }
    return by_iface


def _parse_sysfs_dump(stdout: str) -> Dict[str, Dict[str, str]]:
    out: Dict[str, Dict[str, str]] = {}
    for line in (stdout or "").splitlines():
        parts = line.strip().split("|", 3)
        if len(parts) != 4:
            continue
        name, operstate, mac, dev = parts
        if name.strip() in {"", "*"}:
            continue
        out[name] = {
            "operstate": operstate.strip(),
            "mac": mac.strip(),
            "device_path": dev.strip(),
        }
    return out


def probe_interfaces(
    *,
    runner: Runner,
    host: str,
    deadline: Deadline,
    command_timeout_s: int,
) -> Tuple[List[InterfaceRecord], List[Evidence], Dict[str, str]]:
    if deadline.expired():
        raise TimeoutError("node deadline expired before interfaces probe")

    cmd_timeout = min(command_timeout_s, deadline.remaining_seconds())
    ip_res = runner.run(host, ["ip", "-o", "link", "show"], timeout_s=cmd_timeout)
    ip_data = _parse_ip_link(ip_res.stdout) if ip_res.returncode == 0 else {}

    sysfs_cmd = [
        "bash",
        "-lc",
        "for i in /sys/class/net/*; do n=$(basename \"$i\"); "
        "o=$(cat \"$i/operstate\" 2>/dev/null || true); "
        "m=$(cat \"$i/address\" 2>/dev/null || true); "
        "d=$(readlink -f \"$i/device\" 2>/dev/null || true); "
        "printf '%s|%s|%s|%s\\n' \"$n\" \"$o\" \"$m\" \"$d\"; done",
    ]
    sys_res = runner.run(host, sysfs_cmd, timeout_s=cmd_timeout)
    sys_data = _parse_sysfs_dump(sys_res.stdout) if sys_res.returncode == 0 else {}

    names = sorted(set(ip_data) | set(sys_data))
    records: List[InterfaceRecord] = []
    for name in names:
        merged = {}
        merged.update(ip_data.get(name, {}))
        merged.update(sys_data.get(name, {}))
        operstate = (merged.get("operstate") or "unknown").lower()
        rec = InterfaceRecord(
            name=name,
            operstate=operstate,
            mac=merged.get("mac", ""),
            device_path=merged.get("device_path", ""),
            is_up=operstate in {"up", "unknown"},
        )
        records.append(rec)

    evidence: List[Evidence] = []
    if records:
        evidence.append(
            make_evidence(
                code="interfaces_detected",
                message=f"Detected {len(records)} interfaces",
                source="interfaces",
                confidence="high",
            )
        )
    if ip_res.returncode != 0:
        evidence.append(
            make_evidence(
                code="ip_link_unavailable",
                message="Failed to run ip -o link show",
                source="interfaces",
                confidence="medium",
                data={"stderr": ip_res.stderr.strip()},
            )
        )

    raw = {
        "ip_link_returncode": str(ip_res.returncode),
        "sysfs_returncode": str(sys_res.returncode),
    }
    return records, evidence, raw
