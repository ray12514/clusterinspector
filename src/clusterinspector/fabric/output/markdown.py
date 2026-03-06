from clusterinspector.core.models import FleetReport


def render_markdown(fleet: FleetReport) -> str:
    lines = ["# Fabric Report", ""]
    for node in fleet.nodes:
        lines.append(f"## {node.hostname}")
        lines.append(f"- primary_fabric: {node.primary_fabric}")
        lines.append(f"- health: {node.health}")
        if node.diagnoses:
            lines.append(f"- diagnoses: {', '.join(node.diagnoses)}")
        lines.append("")
    return "\n".join(lines)
