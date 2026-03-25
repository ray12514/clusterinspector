import argparse
import io
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from clusterinspector.profile.cli import run


class TestProfileCli(unittest.TestCase):
    def test_run_writes_single_output_file(self) -> None:
        payload = {
            "schema_version": 1,
            "system": {
                "name": "node01",
                "site": "example.org",
                "platform_class": "cray-nvidia",
                "node_role": "gpu_compute",
                "environment_model": "cray_pe",
                "observed_platform_signals": [],
                "classification_confidence": "high",
            },
            "modules": {
                "active_context": {
                    "source": "active_shell",
                    "prgenv_module": "PrgEnv-nvidia",
                    "gpu_runtime_module": "cudatoolkit/12.4",
                    "mpi_module": "cray-mpich",
                    "compiler_wrapper_family": "cray_wrappers",
                }
            },
        }
        args = argparse.Namespace(
            local=True,
            nodes="",
            format="yaml",
            output="",
            output_dir="",
            context_name="",
            system_name="",
            site="",
            include_gpu=False,
            include_mpi=False,
            include_modules=False,
            profile_action=None,
        )

        with tempfile.TemporaryDirectory() as tempdir:
            args.output = os.path.join(tempdir, "profile.yaml")
            stdout = io.StringIO()
            with patch("clusterinspector.profile.cli.collect_profile", return_value=payload):
                with redirect_stdout(stdout):
                    rc = run(args)

            self.assertEqual(rc, 0)
            self.assertEqual(stdout.getvalue().strip(), args.output)
            with open(args.output, "r", encoding="utf-8") as handle:
                written = handle.read()
            self.assertIn("context_name: prgenv-nvidia-cudatoolkit-12.4", written)
            self.assertIn("platform_class: cray-nvidia", written)

    def test_run_writes_output_dir_with_inferred_names(self) -> None:
        payload = {
            "profiles": [
                {
                    "schema_version": 1,
                    "system": {
                        "name": "node01",
                        "site": "example.org",
                        "platform_class": "cray-nvidia",
                        "node_role": "gpu_compute",
                        "environment_model": "cray_pe",
                        "observed_platform_signals": [],
                        "classification_confidence": "high",
                    },
                    "modules": {
                        "active_context": {
                            "source": "active_shell",
                            "prgenv_module": "PrgEnv-nvidia",
                            "gpu_runtime_module": "",
                            "mpi_module": "cray-mpich",
                            "compiler_wrapper_family": "cray_wrappers",
                        }
                    },
                },
                {
                    "schema_version": 1,
                    "system": {
                        "name": "gpu001",
                        "site": "example.org",
                        "platform_class": "linux-nvidia",
                        "node_role": "gpu_compute",
                        "environment_model": "direct_mpi",
                        "observed_platform_signals": [],
                        "classification_confidence": "high",
                    },
                    "modules": {
                        "active_context": {
                            "source": "active_shell",
                            "prgenv_module": "",
                            "gpu_runtime_module": "cuda/12.4",
                            "mpi_module": "openmpi",
                            "compiler_wrapper_family": "direct_mpi_wrappers",
                        }
                    },
                },
            ]
        }
        args = argparse.Namespace(
            local=True,
            nodes="",
            format="yaml",
            output="",
            output_dir="",
            context_name="",
            system_name="",
            site="",
            include_gpu=False,
            include_mpi=False,
            include_modules=False,
            profile_action=None,
        )

        with tempfile.TemporaryDirectory() as tempdir:
            args.output_dir = tempdir
            stdout = io.StringIO()
            with patch("clusterinspector.profile.cli.collect_profile", return_value=payload):
                with redirect_stdout(stdout):
                    rc = run(args)

            self.assertEqual(rc, 0)
            output_lines = stdout.getvalue().strip().splitlines()
            self.assertEqual(len(output_lines), 2)

            expected_one = os.path.join(tempdir, "gpu-compute--cray-nvidia--prgenv-nvidia.yaml")
            expected_two = os.path.join(tempdir, "gpu-compute--linux-nvidia--openmpi-cuda-12.4.yaml")
            self.assertIn(expected_one, output_lines)
            self.assertIn(expected_two, output_lines)
            self.assertTrue(os.path.exists(expected_one))
            self.assertTrue(os.path.exists(expected_two))

    def test_run_applies_system_and_site_overrides(self) -> None:
        payload = {
            "schema_version": 1,
            "system": {
                "name": "node01",
                "site": "observed.example",
                "platform_class": "linux-nvidia",
                "node_role": "gpu_compute",
                "environment_model": "direct_mpi",
                "observed_platform_signals": [],
                "classification_confidence": "high",
            },
            "modules": {
                "active_context": {
                    "source": "active_shell",
                    "prgenv_module": "",
                    "gpu_runtime_module": "cuda/12.4",
                    "mpi_module": "openmpi",
                    "compiler_wrapper_family": "direct_mpi_wrappers",
                }
            },
        }
        args = argparse.Namespace(
            local=True,
            nodes="",
            format="yaml",
            output="",
            output_dir="",
            context_name="",
            system_name="pilot-cray-h200",
            site="nersc",
            include_gpu=False,
            include_mpi=False,
            include_modules=False,
            profile_action=None,
        )

        stdout = io.StringIO()
        with patch("clusterinspector.profile.cli.collect_profile", return_value=payload):
            with redirect_stdout(stdout):
                rc = run(args)

        self.assertEqual(rc, 0)
        rendered = stdout.getvalue()
        self.assertIn("name: pilot-cray-h200", rendered)
        self.assertIn("site: nersc", rendered)
        self.assertIn("context_name: openmpi-cuda-12.4", rendered)

    def test_run_rejects_output_and_output_dir_together(self) -> None:
        args = argparse.Namespace(
            local=True,
            nodes="",
            format="yaml",
            output="profile.yaml",
            output_dir="profiles",
            context_name="",
            system_name="",
            site="",
            include_gpu=False,
            include_mpi=False,
            include_modules=False,
            profile_action=None,
        )

        stdout = io.StringIO()
        with redirect_stdout(stdout):
            rc = run(args)

        self.assertEqual(rc, 2)
        self.assertIn("use either --output or --output-dir", stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
