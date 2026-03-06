import unittest

from clusterinspector.core.models import InterfaceRecord, NodeReport
from clusterinspector.fabric.classify.fabrics import classify_fabrics


class TestFabricClassify(unittest.TestCase):
    def test_infiniband_from_driver(self) -> None:
        node = NodeReport(
            hostname="node1",
            interfaces=[InterfaceRecord(name="ib0", driver="mlx5_core")],
        )
        classify_fabrics(node)
        self.assertEqual(node.primary_fabric, "infiniband")
        self.assertEqual(node.likely_hpc_fabric, "infiniband")

    def test_unknown_without_signals(self) -> None:
        node = NodeReport(hostname="node2")
        classify_fabrics(node)
        self.assertEqual(node.primary_fabric, "unknown")


if __name__ == "__main__":
    unittest.main()
