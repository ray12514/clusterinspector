import unittest

from clusterinspector.core.models import Evidence, InterfaceRecord, NodeReport
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

    def test_unknown_confidence_not_inflated_by_non_fabric_evidence(self) -> None:
        node = NodeReport(hostname="node3")
        node.evidence = [
            Evidence(code="ip_link_unavailable", message="ip missing", source="interfaces"),
            Evidence(code="lspci_unavailable", message="lspci missing", source="pci"),
            Evidence(code="ethtool_data_unavailable", message="ethtool missing", source="drivers"),
            Evidence(code="rdma_stack_not_visible", message="rdma missing", source="rdma"),
            Evidence(code="fi_info_unavailable", message="fi_info missing", source="libfabric"),
        ]
        classify_fabrics(node)
        self.assertEqual(node.primary_fabric, "unknown")
        self.assertEqual(node.confidence, "low")


if __name__ == "__main__":
    unittest.main()
