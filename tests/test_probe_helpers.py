import unittest

from clusterinspector.fabric.probes.libfabric import _providers_from_full, _providers_from_list
from clusterinspector.fabric.probes.rdma import _active_count, _parse_sysfs_ib


class TestProbeHelpers(unittest.TestCase):
    def test_parse_sysfs_ib(self) -> None:
        parsed = _parse_sysfs_ib("mlx5_0\nmlx5_1\n")
        self.assertEqual(parsed, ["mlx5_0", "mlx5_1"])

    def test_active_count(self) -> None:
        lines = ["link 1/1 state ACTIVE", "link 2/1 state DOWN"]
        self.assertEqual(_active_count(lines), 1)

    def test_provider_parsers(self) -> None:
        l = _providers_from_list("verbs\ntcp\n")
        f = _providers_from_full("provider: cxi\nprovider: verbs\n")
        self.assertIn("verbs", l)
        self.assertIn("cxi", f)


if __name__ == "__main__":
    unittest.main()
