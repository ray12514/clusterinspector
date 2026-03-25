import json
import unittest

from clusterinspector.core.models import FleetReport, NodeReport
from clusterinspector.fabric.output.human import render_human
from clusterinspector.fabric.output.jsonout import render_json
from clusterinspector.fabric.output.markdown import render_markdown


class TestHumanOutput(unittest.TestCase):
    def test_diagnosis_message_rendering(self) -> None:
        node = NodeReport(
            hostname="node01",
            primary_fabric="infiniband",
            management_fabric="ethernet",
            health="impaired",
            confidence="high",
            diagnoses=["rdma_link_inactive"],
        )
        fleet = FleetReport(nodes=[node], summary={})
        text = render_human(fleet, include_diagnoses=True)
        self.assertIn("rdma_link_inactive", text)
        self.assertIn("none appear active", text)

    def test_markdown_and_json_diagnosis_details(self) -> None:
        node = NodeReport(
            hostname="node02",
            primary_fabric="infiniband",
            management_fabric="ethernet",
            health="degraded",
            confidence="medium",
            diagnoses=["rdma_link_inactive", "tcp_fallback_likely"],
        )
        fleet = FleetReport(nodes=[node], summary={})

        markdown = render_markdown(fleet)
        self.assertIn("rdma_link_inactive: RDMA links were detected but none appear active", markdown)
        self.assertIn("tcp_fallback_likely: Likely userspace fallback to TCP path", markdown)

        payload = json.loads(render_json(fleet, include_raw=False))
        details = payload["nodes"][0]["diagnosis_details"]
        self.assertEqual(details[0]["code"], "rdma_link_inactive")
        self.assertIn("none appear active", details[0]["message"])


if __name__ == "__main__":
    unittest.main()
