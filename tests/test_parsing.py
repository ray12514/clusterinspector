import unittest

from clusterinspector.core.parsing import parse_key_value_block, split_pipe_line


class TestParsing(unittest.TestCase):
    def test_parse_key_value_block(self) -> None:
        data = parse_key_value_block("driver: mlx5_core\nfirmware-version: 1.2.3\n")
        self.assertEqual(data.get("driver"), "mlx5_core")
        self.assertEqual(data.get("firmware-version"), "1.2.3")

    def test_split_pipe_line(self) -> None:
        ok, parts = split_pipe_line("a|b|c", expected_parts=3)
        self.assertTrue(ok)
        self.assertEqual(parts, ["a", "b", "c"])


if __name__ == "__main__":
    unittest.main()
