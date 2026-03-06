from typing import List

from clusterinspector.core.models import FleetReport, NodeReport


def _render_node_line(node: NodeReport, include_diagnoses: bool) -> str:
    line = (
        f"{node.hostname} primary={node.primary_fabric} mgmt={node.management_fabric} "
        f"health={node.health} confidence={node.confidence}"
    )
    if include_diagnoses and node.diagnoses:
        line += f" impact={','.join(node.diagnoses)}"
    if not node.ok and node.error:
        line += f" error={node.error}"
    return line


def render_human(
    fleet: FleetReport,
    *,
    include_summary: bool = False,
    include_diagnoses: bool = False,
    include_evidence: bool = False,
) -> str:
    lines: List[str] = []
    for node in fleet.nodes:
        lines.append(_render_node_line(node, include_diagnoses=include_diagnoses))
        if include_evidence and node.evidence:
            for ev in node.evidence:
                lines.append(f"  - {ev.message} ({ev.code})")
    if include_summary:
        lines.append("")
        lines.append("Fleet summary:")
        for key, value in sorted(fleet.summary.items()):
            lines.append(f"  {key}: {value}")
    return "\n".join(lines)
