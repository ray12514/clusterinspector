import argparse
import unittest

from clusterinspector.core.models import CommandResult
from clusterinspector.core.runner import Runner
from clusterinspector.profile.orchestrator import collect_profile


class FakeRunner(Runner):
    def __init__(self, outputs):
        self.outputs = outputs

    def run(self, host, command, timeout_s):
        key = tuple(command)
        stdout = self.outputs.get(key, "")
        return CommandResult(
            host=host,
            command=list(command),
            returncode=0,
            stdout=stdout,
            stderr="",
            started_at="",
            finished_at="",
            duration_s=0.0,
        )


class TestProfileOrchestrator(unittest.TestCase):
    def test_collect_profile_local_nvidia(self) -> None:
        runner = FakeRunner(
            {
                ("hostname", "-f"): "node01.example.org\n",
                ("bash", "-lc", "cat /etc/os-release 2>/dev/null"): 'ID="sles"\nVERSION_ID="15"\n',
                ("uname", "-r"): "6.8.0\n",
                ("getconf", "GNU_LIBC_VERSION"): "glibc 2.31\n",
                ("lscpu",): "Model name: Example CPU\nSocket(s): 2\n",
                (
                    "bash",
                    "-lc",
                    'if [ -n "$SLURM_JOB_ID" ] || command -v sinfo >/dev/null 2>&1; then echo slurm; elif [ -n "$PBS_JOBID" ] || command -v pbsnodes >/dev/null 2>&1; then echo pbs; else echo unknown; fi',
                ): "slurm\n",
                ("nvidia-smi", "--query-gpu=name", "--format=csv,noheader"): "NVIDIA H100\nNVIDIA H100\n",
                ("nvidia-smi", "--query-gpu=compute_cap", "--format=csv,noheader"): "9.0\n9.0\n",
                ("bash", "-lc", "rocm-smi --showproductname 2>/dev/null"): "",
                (
                    "bash",
                    "-lc",
                    "nvidia-smi topo -m 2>/dev/null",
                ): (
                    "        GPU0    GPU1    NIC0    CPU Affinity    NUMA Affinity\n"
                    "GPU0    X       NV18    PIX     0-47            0\n"
                    "GPU1    NV18    X       SYS     48-95           1\n"
                    "NIC0    PIX     SYS     X\n"
                ),
                ("bash", "-lc", "rocm-smi --showtopotype --showtoponuma 2>/dev/null"): "",
                (
                    "bash",
                    "-lc",
                    'printf "PE_ENV=%s\\nCRAYPE_VERSION=%s\\n" "$PE_ENV" "$CRAYPE_VERSION"; for c in cc CC ftn mpicc mpicxx mpifort gcc g++ gfortran; do if command -v "$c" >/dev/null 2>&1; then printf "CMD=%s\\n" "$c"; fi; done',
                ): "PE_ENV=nvidia\nCRAYPE_VERSION=24.07\nCMD=cc\nCMD=CC\nCMD=ftn\n",
                (
                    "bash",
                    "-lc",
                    'printf "LMOD_VERSION=%s\\nMODULESHOME=%s\\nMODULEPATH=%s\\nLOADEDMODULES=%s\\n" "$LMOD_VERSION" "$MODULESHOME" "$MODULEPATH" "$LOADEDMODULES"',
                ): "LMOD_VERSION=8.7\nMODULESHOME=/opt/lmod\nMODULEPATH=/opt/modules\nLOADEDMODULES=PrgEnv-nvidia:cudatoolkit/12.4\n",
                (
                    "bash",
                    "-lc",
                    'printf "OMPI_VERSION=%s\\nMPICH_VERSION=%s\\n" "$OMPI_VERSION" "$MPICH_VERSION"; if command -v mpirun >/dev/null 2>&1; then mpirun --version 2>/dev/null | head -n 1; fi',
                ): "OMPI_VERSION=\nMPICH_VERSION=8.1\nMPICH Version: 8.1\n",
                (
                    "bash",
                    "-lc",
                    'for n in /sys/class/net/*; do [ -e "$n" ] || continue; basename "$n"; done 2>/dev/null | sort',
                ): "hsn0\nlo\n",
                ("bash", "-lc", "fi_info -l 2>/dev/null"): "cxi\n",
            }
        )
        args = argparse.Namespace(local=True, nodes="", format="yaml", include_gpu=False, include_mpi=False, include_modules=False)

        payload = collect_profile(args, runner=runner)
        self.assertEqual(payload["system"]["platform_class"], "cray-nvidia")
        self.assertEqual(payload["system"]["node_role"], "gpu_compute")
        self.assertEqual(payload["system"]["environment_model"], "cray_pe")
        self.assertEqual(payload["system"]["classification_confidence"], "high")
        self.assertIn("cray_pe", payload["system"]["observed_platform_signals"])
        self.assertEqual(payload["hardware"]["gpus"]["count_per_node"], 2)
        self.assertEqual(payload["hardware"]["gpus"]["interconnect_type"], "nvlink")
        self.assertEqual(payload["hardware"]["network"]["fabric"], "slingshot")
        self.assertEqual(payload["hardware"]["network"]["communication_provider"], "cxi")
        self.assertEqual(payload["hardware"]["network"]["mpi_provider"], "mpich")
        self.assertTrue(payload["hardware"]["gpus"]["gpu_nic_topology"])
        self.assertTrue(payload["hardware"]["gpus"]["numa_affinity"])
        self.assertEqual(payload["capabilities"]["t1"]["state"], "inferred")
        self.assertIn("cuda", payload["externals_policy"]["forbid_build"])
        self.assertEqual(payload["vendor_substrate"]["prgenv_module"], "PrgEnv-nvidia")
        self.assertEqual(payload["vendor_substrate"]["mpi_family"], "mpich")
        self.assertEqual(payload["modules"]["active_context"]["prgenv_module"], "PrgEnv-nvidia")
        self.assertEqual(payload["modules"]["active_context"]["compiler_wrapper_family"], "cray_wrappers")
        self.assertEqual(payload["vendor_substrate"]["source"], "active_environment")

    def test_collect_profile_linux_nvidia(self) -> None:
        runner = FakeRunner(
            {
                ("hostname", "-f"): "gpu001.site.example\n",
                ("bash", "-lc", "cat /etc/os-release 2>/dev/null"): 'ID="rhel"\nVERSION_ID="9"\n',
                ("uname", "-r"): "5.14.0\n",
                ("getconf", "GNU_LIBC_VERSION"): "glibc 2.34\n",
                ("lscpu",): "Model name: EPYC\nSocket(s): 2\n",
                (
                    "bash",
                    "-lc",
                    'if [ -n "$SLURM_JOB_ID" ] || command -v sinfo >/dev/null 2>&1; then echo slurm; elif [ -n "$PBS_JOBID" ] || command -v pbsnodes >/dev/null 2>&1; then echo pbs; else echo unknown; fi',
                ): "slurm\n",
                ("nvidia-smi", "--query-gpu=name", "--format=csv,noheader"): "NVIDIA A100\n",
                ("nvidia-smi", "--query-gpu=compute_cap", "--format=csv,noheader"): "8.0\n",
                ("bash", "-lc", "rocm-smi --showproductname 2>/dev/null"): "",
                (
                    "bash",
                    "-lc",
                    "nvidia-smi topo -m 2>/dev/null",
                ): "        GPU0    CPU Affinity    NUMA Affinity\nGPU0    X       0-63            0\n",
                ("bash", "-lc", "rocm-smi --showtopotype --showtoponuma 2>/dev/null"): "",
                (
                    "bash",
                    "-lc",
                    'printf "PE_ENV=%s\\nCRAYPE_VERSION=%s\\n" "$PE_ENV" "$CRAYPE_VERSION"; for c in cc CC ftn mpicc mpicxx mpifort gcc g++ gfortran; do if command -v "$c" >/dev/null 2>&1; then printf "CMD=%s\\n" "$c"; fi; done',
                ): "PE_ENV=\nCRAYPE_VERSION=\nCMD=mpicc\nCMD=mpicxx\nCMD=mpifort\n",
                (
                    "bash",
                    "-lc",
                    'printf "LMOD_VERSION=%s\\nMODULESHOME=%s\\nMODULEPATH=%s\\nLOADEDMODULES=%s\\n" "$LMOD_VERSION" "$MODULESHOME" "$MODULEPATH" "$LOADEDMODULES"',
                ): "LMOD_VERSION=8.7\nMODULESHOME=/opt/lmod\nMODULEPATH=/opt/modules\nLOADEDMODULES=cuda/12.4:openmpi/5.0\n",
                (
                    "bash",
                    "-lc",
                    'printf "OMPI_VERSION=%s\\nMPICH_VERSION=%s\\n" "$OMPI_VERSION" "$MPICH_VERSION"; if command -v mpirun >/dev/null 2>&1; then mpirun --version 2>/dev/null | head -n 1; fi',
                ): "OMPI_VERSION=5.0.1\nMPICH_VERSION=\nOpen MPI 5.0.1\n",
                (
                    "bash",
                    "-lc",
                    'for n in /sys/class/net/*; do [ -e "$n" ] || continue; basename "$n"; done 2>/dev/null | sort',
                ): "ib0\nlo\n",
                ("bash", "-lc", "fi_info -l 2>/dev/null"): "verbs\n",
            }
        )
        args = argparse.Namespace(local=True, nodes="", format="yaml", include_gpu=False, include_mpi=False, include_modules=False)

        payload = collect_profile(args, runner=runner)
        self.assertEqual(payload["system"]["platform_class"], "linux-nvidia")
        self.assertEqual(payload["system"]["environment_model"], "direct_mpi")
        self.assertEqual(payload["system"]["node_role"], "gpu_compute")
        self.assertIn("provider:verbs", payload["system"]["observed_platform_signals"])
        self.assertEqual(payload["vendor_substrate"]["mpi_family"], "openmpi")
        self.assertEqual(payload["modules"]["active_context"]["gpu_runtime_module"], "cuda/12.4")
        self.assertEqual(payload["hardware"]["network"]["fabric"], "infiniband")
        self.assertEqual(payload["hardware"]["network"]["communication_provider"], "verbs")
        self.assertEqual(payload["hardware"]["network"]["mpi_provider"], "openmpi")

    def test_collect_profile_linux_amd(self) -> None:
        runner = FakeRunner(
            {
                ("hostname", "-f"): "gpu-amd01.cluster.example\n",
                ("bash", "-lc", "cat /etc/os-release 2>/dev/null"): 'ID="ubuntu"\nVERSION_ID="24.04"\n',
                ("uname", "-r"): "6.8.0\n",
                ("getconf", "GNU_LIBC_VERSION"): "glibc 2.39\n",
                ("lscpu",): "Model name: EPYC\nSocket(s): 1\n",
                (
                    "bash",
                    "-lc",
                    'if [ -n "$SLURM_JOB_ID" ] || command -v sinfo >/dev/null 2>&1; then echo slurm; elif [ -n "$PBS_JOBID" ] || command -v pbsnodes >/dev/null 2>&1; then echo pbs; else echo unknown; fi',
                ): "pbs\n",
                ("nvidia-smi", "--query-gpu=name", "--format=csv,noheader"): "",
                ("nvidia-smi", "--query-gpu=compute_cap", "--format=csv,noheader"): "",
                ("bash", "-lc", "rocm-smi --showproductname 2>/dev/null"): "GPU[0]          : Card series: Instinct MI300X\n",
                ("bash", "-lc", "nvidia-smi topo -m 2>/dev/null"): "",
                (
                    "bash",
                    "-lc",
                    "rocm-smi --showtopotype --showtoponuma 2>/dev/null",
                ): (
                    "GPU0 -> GPU1 : XGMI\n"
                    "GPU0 NUMA Node: 0\n"
                    "GPU1 NUMA Node: 1\n"
                ),
                (
                    "bash",
                    "-lc",
                    'printf "PE_ENV=%s\\nCRAYPE_VERSION=%s\\n" "$PE_ENV" "$CRAYPE_VERSION"; for c in cc CC ftn mpicc mpicxx mpifort gcc g++ gfortran; do if command -v "$c" >/dev/null 2>&1; then printf "CMD=%s\\n" "$c"; fi; done',
                ): "PE_ENV=\nCRAYPE_VERSION=\nCMD=mpicc\nCMD=mpicxx\nCMD=mpifort\n",
                (
                    "bash",
                    "-lc",
                    'printf "LMOD_VERSION=%s\\nMODULESHOME=%s\\nMODULEPATH=%s\\nLOADEDMODULES=%s\\n" "$LMOD_VERSION" "$MODULESHOME" "$MODULEPATH" "$LOADEDMODULES"',
                ): "LMOD_VERSION=8.7\nMODULESHOME=/opt/lmod\nMODULEPATH=/opt/modules\nLOADEDMODULES=rocm/6.3:openmpi/5.0\n",
                (
                    "bash",
                    "-lc",
                    'printf "OMPI_VERSION=%s\\nMPICH_VERSION=%s\\n" "$OMPI_VERSION" "$MPICH_VERSION"; if command -v mpirun >/dev/null 2>&1; then mpirun --version 2>/dev/null | head -n 1; fi',
                ): "OMPI_VERSION=5.0.1\nMPICH_VERSION=\nOpen MPI 5.0.1\n",
                (
                    "bash",
                    "-lc",
                    'for n in /sys/class/net/*; do [ -e "$n" ] || continue; basename "$n"; done 2>/dev/null | sort',
                ): "eth0\nlo\n",
                ("bash", "-lc", "fi_info -l 2>/dev/null"): "",
            }
        )
        args = argparse.Namespace(local=True, nodes="", format="yaml", include_gpu=False, include_mpi=False, include_modules=False)

        payload = collect_profile(args, runner=runner)
        self.assertEqual(payload["system"]["platform_class"], "linux-amd")
        self.assertEqual(payload["system"]["environment_model"], "direct_mpi")
        self.assertEqual(payload["system"]["node_role"], "gpu_compute")
        self.assertIn("gpu_vendor:amd", payload["system"]["observed_platform_signals"])
        self.assertEqual(payload["vendor_substrate"]["rocm_module"], "rocm/6.3")
        self.assertEqual(payload["hardware"]["gpus"]["interconnect_type"], "xgmi")
        self.assertEqual(payload["hardware"]["network"]["fabric"], "ethernet")
        self.assertEqual(payload["hardware"]["network"]["communication_provider"], "unknown")

    def test_collect_profile_cpu_only_cray_environment(self) -> None:
        runner = FakeRunner(
            {
                ("hostname", "-f"): "login01.site.example\n",
                ("bash", "-lc", "cat /etc/os-release 2>/dev/null"): 'ID="sles"\nVERSION_ID="15"\n',
                ("uname", "-r"): "6.8.0\n",
                ("getconf", "GNU_LIBC_VERSION"): "glibc 2.31\n",
                ("lscpu",): "Model name: EPYC\nSocket(s): 2\n",
                (
                    "bash",
                    "-lc",
                    'if [ -n "$SLURM_JOB_ID" ] || command -v sinfo >/dev/null 2>&1; then echo slurm; elif [ -n "$PBS_JOBID" ] || command -v pbsnodes >/dev/null 2>&1; then echo pbs; else echo unknown; fi',
                ): "unknown\n",
                ("nvidia-smi", "--query-gpu=name", "--format=csv,noheader"): "",
                ("nvidia-smi", "--query-gpu=compute_cap", "--format=csv,noheader"): "",
                ("bash", "-lc", "rocm-smi --showproductname 2>/dev/null"): "",
                ("bash", "-lc", "nvidia-smi topo -m 2>/dev/null"): "",
                ("bash", "-lc", "rocm-smi --showtopotype --showtoponuma 2>/dev/null"): "",
                (
                    "bash",
                    "-lc",
                    'printf "PE_ENV=%s\\nCRAYPE_VERSION=%s\\n" "$PE_ENV" "$CRAYPE_VERSION"; for c in cc CC ftn mpicc mpicxx mpifort gcc g++ gfortran; do if command -v "$c" >/dev/null 2>&1; then printf "CMD=%s\\n" "$c"; fi; done',
                ): "PE_ENV=gnu\nCRAYPE_VERSION=24.07\nCMD=cc\nCMD=CC\nCMD=ftn\n",
                (
                    "bash",
                    "-lc",
                    'printf "LMOD_VERSION=%s\\nMODULESHOME=%s\\nMODULEPATH=%s\\nLOADEDMODULES=%s\\n" "$LMOD_VERSION" "$MODULESHOME" "$MODULEPATH" "$LOADEDMODULES"',
                ): "LMOD_VERSION=8.7\nMODULESHOME=/opt/lmod\nMODULEPATH=/opt/modules\nLOADEDMODULES=PrgEnv-gnu\n",
                (
                    "bash",
                    "-lc",
                    'printf "OMPI_VERSION=%s\\nMPICH_VERSION=%s\\n" "$OMPI_VERSION" "$MPICH_VERSION"; if command -v mpirun >/dev/null 2>&1; then mpirun --version 2>/dev/null | head -n 1; fi',
                ): "OMPI_VERSION=\nMPICH_VERSION=8.1\nMPICH Version: 8.1\n",
                (
                    "bash",
                    "-lc",
                    'for n in /sys/class/net/*; do [ -e "$n" ] || continue; basename "$n"; done 2>/dev/null | sort',
                ): "eth0\nlo\n",
                ("bash", "-lc", "fi_info -l 2>/dev/null"): "cxi\n",
            }
        )
        args = argparse.Namespace(local=True, nodes="", format="yaml", include_gpu=False, include_mpi=False, include_modules=False)

        payload = collect_profile(args, runner=runner)
        self.assertEqual(payload["system"]["platform_class"], "unknown")
        self.assertEqual(payload["system"]["environment_model"], "cray_pe")
        self.assertEqual(payload["system"]["node_role"], "login_or_service")
        self.assertEqual(payload["system"]["classification_confidence"], "medium")
        self.assertIn("cray_pe", payload["system"]["observed_platform_signals"])

    def test_collect_profile_cray_amd(self) -> None:
        runner = FakeRunner(
            {
                ("hostname", "-f"): "mi300x001.site.example\n",
                ("bash", "-lc", "cat /etc/os-release 2>/dev/null"): 'ID="sles"\nVERSION_ID="15"\n',
                ("uname", "-r"): "6.8.0\n",
                ("getconf", "GNU_LIBC_VERSION"): "glibc 2.31\n",
                ("lscpu",): "Model name: EPYC\nSocket(s): 2\n",
                (
                    "bash",
                    "-lc",
                    'if [ -n "$SLURM_JOB_ID" ] || command -v sinfo >/dev/null 2>&1; then echo slurm; elif [ -n "$PBS_JOBID" ] || command -v pbsnodes >/dev/null 2>&1; then echo pbs; else echo unknown; fi',
                ): "slurm\n",
                ("nvidia-smi", "--query-gpu=name", "--format=csv,noheader"): "",
                ("nvidia-smi", "--query-gpu=compute_cap", "--format=csv,noheader"): "",
                ("bash", "-lc", "rocm-smi --showproductname 2>/dev/null"): (
                    "GPU[0]          : Card series: Instinct MI300X\n"
                    "GPU[1]          : Card series: Instinct MI300X\n"
                ),
                ("bash", "-lc", "nvidia-smi topo -m 2>/dev/null"): "",
                (
                    "bash",
                    "-lc",
                    "rocm-smi --showtopotype --showtoponuma 2>/dev/null",
                ): (
                    "GPU0 -> GPU1 : XGMI\n"
                    "GPU0 NUMA Node: 0\n"
                    "GPU1 NUMA Node: 1\n"
                    "GPU0 -> hsn0 : PIX\n"
                ),
                (
                    "bash",
                    "-lc",
                    'printf "PE_ENV=%s\\nCRAYPE_VERSION=%s\\n" "$PE_ENV" "$CRAYPE_VERSION"; for c in cc CC ftn mpicc mpicxx mpifort gcc g++ gfortran; do if command -v "$c" >/dev/null 2>&1; then printf "CMD=%s\\n" "$c"; fi; done',
                ): "PE_ENV=cray\nCRAYPE_VERSION=25.03\nCMD=cc\nCMD=CC\nCMD=ftn\n",
                (
                    "bash",
                    "-lc",
                    'printf "LMOD_VERSION=%s\\nMODULESHOME=%s\\nMODULEPATH=%s\\nLOADEDMODULES=%s\\n" "$LMOD_VERSION" "$MODULESHOME" "$MODULEPATH" "$LOADEDMODULES"',
                ): "LMOD_VERSION=8.7\nMODULESHOME=/opt/lmod\nMODULEPATH=/opt/modules\nLOADEDMODULES=PrgEnv-cray:rocm/6.3:cray-mpich\n",
                (
                    "bash",
                    "-lc",
                    'printf "OMPI_VERSION=%s\\nMPICH_VERSION=%s\\n" "$OMPI_VERSION" "$MPICH_VERSION"; if command -v mpirun >/dev/null 2>&1; then mpirun --version 2>/dev/null | head -n 1; fi',
                ): "OMPI_VERSION=\nMPICH_VERSION=8.1.32\nMPICH Version: 8.1.32\n",
                (
                    "bash",
                    "-lc",
                    'for n in /sys/class/net/*; do [ -e "$n" ] || continue; basename "$n"; done 2>/dev/null | sort',
                ): "hsn0\nlo\n",
                ("bash", "-lc", "fi_info -l 2>/dev/null"): "cxi\n",
            }
        )
        args = argparse.Namespace(local=True, nodes="", format="yaml", include_gpu=False, include_mpi=False, include_modules=False)

        payload = collect_profile(args, runner=runner)
        self.assertEqual(payload["system"]["platform_class"], "cray-amd")
        self.assertEqual(payload["system"]["environment_model"], "cray_pe")
        self.assertEqual(payload["system"]["node_role"], "gpu_compute")
        self.assertEqual(payload["system"]["classification_confidence"], "high")
        self.assertIn("cray_pe", payload["system"]["observed_platform_signals"])
        self.assertIn("gpu_vendor:amd", payload["system"]["observed_platform_signals"])
        self.assertIn("provider:cxi", payload["system"]["observed_platform_signals"])
        self.assertEqual(payload["hardware"]["gpus"]["vendor"], "amd")
        self.assertEqual(payload["hardware"]["gpus"]["count_per_node"], 2)
        self.assertEqual(payload["vendor_substrate"]["prgenv_module"], "PrgEnv-cray")
        self.assertEqual(payload["vendor_substrate"]["mpi_family"], "mpich")
        self.assertEqual(payload["vendor_substrate"]["rocm_module"], "rocm/6.3")
        self.assertEqual(payload["modules"]["active_context"]["gpu_runtime_module"], "rocm/6.3")
        self.assertEqual(payload["modules"]["active_context"]["compiler_wrapper_family"], "cray_wrappers")
        self.assertEqual(payload["hardware"]["gpus"]["interconnect_type"], "xgmi")
        self.assertEqual(payload["hardware"]["network"]["fabric"], "slingshot")
        self.assertEqual(payload["hardware"]["network"]["communication_provider"], "cxi")
        self.assertIn("rocm", payload["externals_policy"]["forbid_build"])


if __name__ == "__main__":
    unittest.main()
