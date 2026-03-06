from typing import Dict, List, Tuple

from clusterinspector.core.models import Evidence


def probe_libfabric(*args, **kwargs) -> Tuple[Dict[str, object], List[Evidence]]:
    return {}, []
