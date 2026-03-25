from typing import Dict, List

from clusterinspector.core.runner import Runner


_COMPILER_CMD = (
    'printf "PE_ENV=%s\\nCRAYPE_VERSION=%s\\n" "$PE_ENV" "$CRAYPE_VERSION"; '
    'for c in cc CC ftn mpicc mpicxx mpifort gcc g++ gfortran; do '
    'if command -v "$c" >/dev/null 2>&1; then printf "CMD=%s\\n" "$c"; fi; '
    "done"
)


def probe_compiler(runner: Runner, host: str, timeout_s: int = 10) -> Dict[str, object]:
    result = runner.run(host, ["bash", "-lc", _COMPILER_CMD], timeout_s=timeout_s)

    env: Dict[str, str] = {}
    commands: List[str] = []
    for raw in (result.stdout or "").splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("CMD="):
            commands.append(line.split("=", 1)[1])
            continue
        if "=" in line:
            key, value = line.split("=", 1)
            env[key] = value.strip()

    prgenv_module = ""
    if env.get("PE_ENV"):
        prgenv_module = f"PrgEnv-{env['PE_ENV']}"

    if {"cc", "CC", "ftn"}.issubset(set(commands)):
        wrappers = ["cc", "CC", "ftn"]
    elif {"mpicc", "mpicxx", "mpifort"}.issubset(set(commands)):
        wrappers = ["mpicc", "mpicxx", "mpifort"]
    else:
        wrappers = commands

    return {
        "prgenv_module": prgenv_module,
        "compiler_wrappers": wrappers,
        "is_cray": bool(prgenv_module or env.get("CRAYPE_VERSION")),
    }
