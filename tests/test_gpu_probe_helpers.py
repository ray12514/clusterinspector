import unittest

from clusterinspector.fabric.probes.gpu import _contains_direct_tokens, _contains_staged_tokens


class TestGpuProbeHelpers(unittest.TestCase):
    def test_direct_tokens(self) -> None:
        self.assertTrue(_contains_direct_tokens(["GPU0 PIX GPU1", "NIC GPUDirect"]))
        self.assertFalse(_contains_direct_tokens(["GPU0 SYS GPU1"]))

    def test_staged_tokens(self) -> None:
        self.assertTrue(_contains_staged_tokens(["GPU0 SYS GPU1"]))
        self.assertFalse(_contains_staged_tokens(["GPU0 PIX GPU1"]))


if __name__ == "__main__":
    unittest.main()
