from clusterinspector.core.models import FleetReport
from clusterinspector.fabric.diagnosis import diagnosis_details


def render_markdown(fleet: FleetReport) -> str:
    lines = ["# Fabric Report", ""]
    for node in fleet.nodes:
        lines.append(f"## {node.hostname}")
        lines.append(f"- primary_fabric: {node.primary_fabric}")
        lines.append(f"- health: {node.health}")
        if node.diagnoses:
            rendered = [f"{item['code']}: {item['message']}" for item in diagnosis_details(node.diagnoses)]
            lines.append(f"- diagnoses: {'; '.join(rendered)}")
        lines.append("")
    return "\n".join(lines)
