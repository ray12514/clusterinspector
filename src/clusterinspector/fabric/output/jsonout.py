import json

from clusterinspector.core.models import FleetReport


def render_json(fleet: FleetReport, *, include_raw: bool = False) -> str:
    return json.dumps(fleet.to_dict(include_raw=include_raw), indent=2, sort_keys=True)
