import unittest

from clusterinspector.core.models import NodeReport
from clusterinspector.fabric.classify.health import classify_health
from clusterinspector.fabric.classify.impact import classify_impact


class TestFabricHealthImpact(unittest.TestCase):
    def test_impaired_when_rdma_links_inactive(self) -> None:
        node = NodeReport(hostname="n1", likely_hpc_fabric="infiniband")
        node.raw["rdma"] = {
            "has_rdma_stack": True,
            "rdma_link_count": 2,
            "active_link_count": 0,
        }
        node.raw["libfabric"] = {
            "providers": ["verbs"],
            "has_fast_provider": True,
        }
        classify_health(node)
        self.assertEqual(node.health, "impaired")
        self.assertIn("rdma_link_inactive", node.diagnoses)

    def test_tcp_fallback_likely_without_fast_provider(self) -> None:
        node = NodeReport(hostname="n2", likely_hpc_fabric="slingshot")
        node.raw["rdma"] = {
            "has_rdma_stack": True,
            "rdma_link_count": 1,
            "active_link_count": 1,
        }
        node.raw["libfabric"] = {
            "providers": ["tcp"],
            "has_fast_provider": False,
        }
        classify_health(node)
        classify_impact(node)
        self.assertIn("tcp_fallback_likely", node.diagnoses)
        self.assertIn(node.health, {"degraded", "impaired"})


if __name__ == "__main__":
    unittest.main()
