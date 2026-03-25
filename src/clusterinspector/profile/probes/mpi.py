from typing import Dict

from clusterinspector.core.runner import Runner


_MPI_CMD = (
    'printf "OMPI_VERSION=%s\\nMPICH_VERSION=%s\\n" "$OMPI_VERSION" "$MPICH_VERSION"; '
    'if command -v mpirun >/dev/null 2>&1; then mpirun --version 2>/dev/null | head -n 1; fi'
)


def probe_mpi(runner: Runner, host: str, timeout_s: int = 10) -> Dict[str, str]:
    result = runner.run(host, ["bash", "-lc", _MPI_CMD], timeout_s=timeout_s)

    ompi_version = ""
    mpich_version = ""
    version_line = ""
    for raw in (result.stdout or "").splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("OMPI_VERSION="):
            ompi_version = line.split("=", 1)[1]
        elif line.startswith("MPICH_VERSION="):
            mpich_version = line.split("=", 1)[1]
        elif not version_line:
            version_line = line

    family = "unknown"
    module_name = ""
    if ompi_version or "open mpi" in version_line.lower():
        family = "openmpi"
        module_name = "openmpi"
    elif mpich_version or "mpich" in version_line.lower() or "hydra" in version_line.lower():
        family = "mpich"
        module_name = "mpich"

    return {
        "family": family,
        "version": ompi_version or mpich_version,
        "version_text": version_line,
        "module_name": module_name,
    }
