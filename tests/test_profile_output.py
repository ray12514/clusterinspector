import unittest

from clusterinspector.profile.output.human import render_human
from clusterinspector.profile.output.yamlout import render_yaml


class TestProfileOutput(unittest.TestCase):
    def test_render_yaml_nested_profile(self) -> None:
        profile = {
            "system": {"name": "node01", "platform_class": "linux-nvidia"},
            "hardware": {
                "gpus": {"vendor": "nvidia", "count_per_node": 4},
                "nics": [{"name": "ib0", "fabric": "infiniband"}],
            },
        }

        text = render_yaml(profile)
        self.assertIn("system:", text)
        self.assertIn("platform_class: linux-nvidia", text)
        self.assertIn("name: ib0", text)

    def test_render_human_collection(self) -> None:
        payload = {
            "profiles": [
                {
                    "system": {
                        "name": "node01",
                        "platform_class": "cray-nvidia",
                        "node_role": "gpu_compute",
                        "environment_model": "cray_pe",
                        "classification_confidence": "high",
                        "observed_platform_signals": ["cray_pe", "gpu_vendor:nvidia"],
                        "site": "example.org",
                    },
                    "scheduler": {"type": "slurm"},
                    "modules": {
                        "active_context": {
                            "prgenv_module": "PrgEnv-nvidia",
                            "compiler_wrapper_family": "cray_wrappers",
                        }
                    },
                    "hardware": {
                        "gpus": {
                            "vendor": "nvidia",
                            "model": "H100",
                            "count_per_node": 4,
                            "interconnect_type": "nvlink",
                        },
                        "network": {
                            "fabric": "slingshot",
                            "communication_provider": "cxi",
                        },
                    },
                    "vendor_substrate": {"compiler_wrappers": ["cc", "CC", "ftn"]},
                    "capabilities": {
                        "t0": {"state": "observed"},
                        "t1": {"state": "inferred"},
                        "t2": {"state": "observed"},
                        "t3": {"state": "unknown"},
                    },
                }
            ]
        }

        text = render_human(payload)
        self.assertIn("Profiles:", text)
        self.assertIn("Platform class: cray-nvidia", text)
        self.assertIn("Node role: gpu_compute", text)
        self.assertIn("Environment model: cray_pe", text)
        self.assertIn("Classification confidence: high", text)
        self.assertIn("Active context: PrgEnv-nvidia", text)
        self.assertIn("Signals: cray_pe, gpu_vendor:nvidia", text)
        self.assertIn("GPU interconnect: nvlink", text)
        self.assertIn("Network fabric: slingshot", text)
        self.assertIn("Communication provider: cxi", text)
        self.assertIn("T1: inferred", text)


if __name__ == "__main__":
    unittest.main()
