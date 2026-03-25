import json

from clusterinspector.core.models import FleetReport
from clusterinspector.fabric.diagnosis import diagnosis_details


def render_json(fleet: FleetReport, *, include_raw: bool = False) -> str:
    payload = fleet.to_dict(include_raw=include_raw)
    for node in payload.get("nodes", []):
        codes = node.get("diagnoses", [])
        node["diagnosis_details"] = diagnosis_details(codes)
    return json.dumps(payload, indent=2, sort_keys=True)
