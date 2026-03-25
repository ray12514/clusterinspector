from typing import Dict

from clusterinspector.core.runner import Runner


_SCHEDULER_CMD = (
    'if [ -n "$SLURM_JOB_ID" ] || command -v sinfo >/dev/null 2>&1; then echo slurm; '
    'elif [ -n "$PBS_JOBID" ] || command -v pbsnodes >/dev/null 2>&1; then echo pbs; '
    "else echo unknown; fi"
)


def _parse_os_release(stdout: str) -> Dict[str, str]:
    data: Dict[str, str] = {}
    for raw in (stdout or "").splitlines():
        line = raw.strip()
        if not line or "=" not in line:
            continue
        key, value = line.split("=", 1)
        data[key] = value.strip().strip('"')
    return {
        "distro": data.get("ID", "unknown"),
        "version": data.get("VERSION_ID", ""),
    }


def _parse_lscpu(stdout: str) -> Dict[str, object]:
    model = ""
    sockets = 0
    for raw in (stdout or "").splitlines():
        if ":" not in raw:
            continue
        key, value = [part.strip() for part in raw.split(":", 1)]
        if key == "Model name":
            model = value
        elif key == "Socket(s)":
            try:
                sockets = int(value)
            except ValueError:
                sockets = 0
    return {"model": model, "sockets_per_node": sockets}


def _site_from_fqdn(name: str) -> str:
    parts = (name or "").strip().split(".")
    if len(parts) > 1 and ".".join(parts[1:]) != "local":
        return ".".join(parts[1:])
    return "unknown"


def _launcher_for_scheduler(scheduler_type: str) -> str:
    if scheduler_type == "slurm":
        return "srun"
    if scheduler_type == "pbs":
        return "mpirun"
    return ""


def probe_system(runner: Runner, host: str, timeout_s: int = 10) -> Dict[str, object]:
    hostname = runner.run(host, ["hostname", "-f"], timeout_s=timeout_s)
    os_release = runner.run(host, ["bash", "-lc", "cat /etc/os-release 2>/dev/null"], timeout_s=timeout_s)
    kernel = runner.run(host, ["uname", "-r"], timeout_s=timeout_s)
    glibc = runner.run(host, ["getconf", "GNU_LIBC_VERSION"], timeout_s=timeout_s)
    lscpu = runner.run(host, ["lscpu"], timeout_s=timeout_s)
    scheduler = runner.run(host, ["bash", "-lc", _SCHEDULER_CMD], timeout_s=timeout_s)

    fqdn = (hostname.stdout or host).strip() or host
    scheduler_type = (scheduler.stdout or "unknown").strip() or "unknown"
    parsed_os = _parse_os_release(os_release.stdout)

    return {
        "hostname": fqdn.split(".", 1)[0],
        "fqdn": fqdn,
        "site": _site_from_fqdn(fqdn),
        "os": {
            **parsed_os,
            "kernel": (kernel.stdout or "").strip(),
            "glibc_version": (glibc.stdout or "").strip().replace("glibc ", ""),
        },
        "cpu": _parse_lscpu(lscpu.stdout),
        "scheduler": {
            "type": scheduler_type,
            "launcher_in_alloc": _launcher_for_scheduler(scheduler_type),
        },
    }
