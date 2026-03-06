import unittest

from clusterinspector.fabric.probes.interfaces import _parse_ip_link, _parse_sysfs_dump


class TestInterfaceParsing(unittest.TestCase):
    def test_parse_ip_link(self) -> None:
        sample = "1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 state UNKNOWN mode DEFAULT group default qlen 1000 link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00\n2: ib0: <BROADCAST,UP,LOWER_UP> mtu 2044 state UP mode DEFAULT group default qlen 256 link/infiniband 80:00:00:00:00:00:00:00 brd 00:ff:ff:ff:ff:12:34:56\n"
        parsed = _parse_ip_link(sample)
        self.assertIn("ib0", parsed)
        self.assertEqual(parsed["ib0"]["operstate"], "up")

    def test_parse_sysfs_dump(self) -> None:
        sample = "ib0|up|aa:bb:cc:dd:ee:ff|/sys/devices/pci0000:00/0000:00:01.0\n"
        parsed = _parse_sysfs_dump(sample)
        self.assertEqual(parsed["ib0"]["device_path"], "/sys/devices/pci0000:00/0000:00:01.0")


if __name__ == "__main__":
    unittest.main()
