from typing import Dict, List, Tuple

from clusterinspector.core.evidence import make_evidence
from clusterinspector.core.models import Evidence, InterfaceRecord
from clusterinspector.core.parsing import parse_key_value_block
from clusterinspector.core.runner import Runner
from clusterinspector.core.timeouts import Deadline


def probe_drivers(
    *,
    runner: Runner,
    host: str,
    interfaces: List[InterfaceRecord],
    deadline: Deadline,
    command_timeout_s: int,
) -> Tuple[Dict[str, Dict[str, str]], List[Evidence]]:
    if deadline.expired():
        raise TimeoutError("node deadline expired before drivers probe")

    chosen = [i.name for i in interfaces if i.name != "lo"]
    out: Dict[str, Dict[str, str]] = {}
    evidence: List[Evidence] = []

    for ifname in chosen:
        if deadline.expired():
            break
        cmd_timeout = min(command_timeout_s, deadline.remaining_seconds())
        res = runner.run(host, ["ethtool", "-i", ifname], timeout_s=cmd_timeout)
        if res.returncode != 0:
            continue

        parsed = parse_key_value_block(res.stdout)
        out[ifname] = parsed
        driver = parsed.get("driver", "")
        if driver:
            evidence.append(
                make_evidence(
                    code="nic_driver_detected",
                    message=f"Interface {ifname} uses driver {driver}",
                    source="drivers",
                    confidence="high",
                    data={"iface": ifname, "driver": driver},
                )
            )
        for rec in interfaces:
            if rec.name == ifname:
                rec.driver = driver
                rec.bus_info = parsed.get("bus-info", "")
                rec.firmware = parsed.get("firmware-version", "")

    if not out:
        evidence.append(
            make_evidence(
                code="ethtool_data_unavailable",
                message="No ethtool -i output collected",
                source="drivers",
                confidence="low",
            )
        )
    return out, evidence
