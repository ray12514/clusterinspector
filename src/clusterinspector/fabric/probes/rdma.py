from typing import Dict, List, Tuple

from clusterinspector.core.models import Evidence


def probe_rdma(*args, **kwargs) -> Tuple[Dict[str, object], List[Evidence]]:
    return {}, []
