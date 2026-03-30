from datetime import datetime, timezone
from typing import Any, Dict, List


PROFILE_SCHEMA_VERSION = 1


def capability_state(state: str = "unknown", **extra: Any) -> Dict[str, Any]:
    payload: Dict[str, Any] = {"state": state}
    payload.update(extra)
    return payload


def empty_profile(hostname: str) -> Dict[str, Any]:
    return {
        "schema_version": PROFILE_SCHEMA_VERSION,
        "system": {
            "name": hostname,
            "site": "unknown",
            "platform_class": "unknown",
            "node_role": "unknown",
            "environment_model": "unknown",
            "observed_platform_signals": [],
            "classification_confidence": "low",
        },
        "os": {},
        "modules": {
            "system": "unknown",
            "modulepath": "",
            "hierarchy_notes": "",
            "loaded": [],
            "active_context": {
                "source": "active_shell",
                "context_name": "",
                "prgenv_module": "",
                "gpu_runtime_module": "",
                "mpi_module": "",
                "compiler_wrapper_family": "unknown",
            },
        },
        "scheduler": {"type": "unknown"},
        "hardware": {
            "cpu": {},
            "gpus": {
                "vendor": "unknown",
                "model": "",
                "count_per_node": 0,
                "compute_capability": "",
                "interconnect_type": "",
                "interconnect_topology": "",
                "gpu_nic_topology": "",
                "numa_affinity": [],
            },
            "nics": [],
            "network": {
                "fabric": "unknown",
                "communication_provider": "unknown",
                "available_providers": [],
                "mpi_provider": "unknown",
            },
        },
        "vendor_substrate": {
            "prgenv_module": "",
            "compiler_wrappers": [],
            "mpi_module": "",
            "mpi_family": "unknown",
            "cuda_module": "",
            "rocm_module": "",
            "source": "unknown",
        },
        "externals_policy": {
            "forbid_build": [],
            "module_based_externals": False,
        },
        "capabilities": {
            "t0": capability_state(),
            "t1": capability_state(),
            "t2": capability_state(),
            "t3": capability_state(),
            "mpi_gpu_aware": capability_state(),
            "gpudirect_rdma": capability_state(),
            "dl_collectives": capability_state(),
        },
        "monitoring": {},
        "validation_evidence": {
            "last_validated": "",
            "validation_layers": [],
            "tests_run": [],
        },
    }


def wrap_profiles(profiles: List[Dict[str, Any]]) -> Dict[str, Any]:
    if len(profiles) == 1:
        return profiles[0]
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "profiles": profiles,
    }
