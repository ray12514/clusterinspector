from typing import Dict, List, Tuple

from clusterinspector.core.models import Evidence


def probe_gpu_hints(*args, **kwargs) -> Tuple[Dict[str, object], List[Evidence]]:
    return {}, []
