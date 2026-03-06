import unittest

from clusterinspector.core.models import FleetReport, NodeReport
from clusterinspector.fabric.output.human import render_human


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


if __name__ == "__main__":
    unittest.main()
