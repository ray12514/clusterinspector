import os
import socket
import subprocess
from typing import List, Optional


def _short(name: str) -> str:
    return (name or "").strip().split(".", 1)[0]


def _from_hosts_file(path: str) -> List[str]:
    hosts: List[str] = []
    with open(path, "r", encoding="utf-8") as handle:
        for raw in handle:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            hosts.append(_short(line))
    return hosts


def _from_nodes_arg(nodes: str) -> List[str]:
    return [_short(x) for x in nodes.split(",") if x.strip()]


def _from_scheduler(scheduler: str) -> List[str]:
    if scheduler == "slurm":
        try:
            proc = subprocess.run(
                ["sinfo", "-N", "-h", "-o", "%N"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
                timeout=20,
            )
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return []
        if proc.returncode != 0:
            return []
        return sorted({_short(x) for x in proc.stdout.splitlines() if x.strip()})

    if scheduler == "pbs":
        try:
            proc = subprocess.run(
                ["pbsnodes", "-a"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
                timeout=20,
            )
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return []
        if proc.returncode != 0:
            return []
        hosts: List[str] = []
        for line in proc.stdout.splitlines():
            if not line.strip():
                continue
            if line and (not line[0].isspace()) and (":" not in line):
                hosts.append(_short(line.strip()))
        return sorted(set(hosts))

    return []


def resolve_hosts(
    *,
    local: bool,
    nodes: Optional[str],
    hosts_file: Optional[str],
    scheduler: Optional[str],
) -> List[str]:
    if local:
        return [_short(socket.gethostname())]

    resolved: List[str] = []
    if nodes:
        resolved.extend(_from_nodes_arg(nodes))
    if hosts_file:
        if not os.path.exists(hosts_file):
            raise FileNotFoundError(f"hosts file not found: {hosts_file}")
        resolved.extend(_from_hosts_file(hosts_file))
    if scheduler and scheduler != "none":
        resolved.extend(_from_scheduler(scheduler))

    deduped: List[str] = []
    seen = set()
    for host in resolved:
        if host and host not in seen:
            seen.add(host)
            deduped.append(host)
    return deduped
