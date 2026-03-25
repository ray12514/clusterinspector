from typing import Dict, List

from clusterinspector.core.runner import Runner


_MODULES_CMD = (
    'printf "LMOD_VERSION=%s\\nMODULESHOME=%s\\nMODULEPATH=%s\\nLOADEDMODULES=%s\\n" '
    '"$LMOD_VERSION" "$MODULESHOME" "$MODULEPATH" "$LOADEDMODULES"'
)


def probe_modules(runner: Runner, host: str, timeout_s: int = 10) -> Dict[str, object]:
    result = runner.run(host, ["bash", "-lc", _MODULES_CMD], timeout_s=timeout_s)

    env: Dict[str, str] = {}
    for raw in (result.stdout or "").splitlines():
        line = raw.strip()
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        env[key] = value.strip()

    if env.get("LMOD_VERSION"):
        system_type = "lmod"
    elif env.get("MODULESHOME"):
        system_type = "tcl"
    else:
        system_type = "unknown"

    loaded_modules = [item for item in env.get("LOADEDMODULES", "").split(":") if item]
    notes: List[str] = []
    if any(item.startswith("PrgEnv-") for item in loaded_modules):
        notes.append("PrgEnv hierarchy detected")

    return {
        "system": system_type,
        "modulepath": env.get("MODULEPATH", ""),
        "hierarchy_notes": "; ".join(notes),
        "loaded": loaded_modules,
    }
