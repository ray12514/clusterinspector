from typing import Any, Dict, List, Tuple


# MPI module prefix → Spack package name
_MPI_SPACK_NAMES = [
    ("cray-mpich", "cray-mpich"),
    ("mvapich2", "mvapich2"),
    ("mvapich", "mvapich2"),
    ("openmpi", "openmpi"),
    ("mpich", "mpich"),
]

# CPE module prefix → (Spack package name, spec variant suffix)
_CPE_LIBS: List[Tuple[str, str, str]] = [
    ("cray-libsci", "cray-libsci", ""),
    ("cray-hdf5-parallel", "hdf5", " +mpi +hl"),
    ("cray-fftw", "fftw", ""),
    ("cray-netcdf-hdf5parallel", "netcdf-c", " +mpi +parallel-netcdf"),
    ("cray-parallel-netcdf", "parallel-netcdf", ""),
    ("cray-pals", "cray-pals", ""),
]


def _parse_version(module_name: str) -> str:
    """Return the version from 'pkg/1.2.3' or '' if no slash."""
    return module_name.split("/", 1)[1] if "/" in module_name else ""


def _mpi_spack_name(mpi_family: str, mpi_module: str) -> str:
    needle = (mpi_family or mpi_module or "").lower()
    for prefix, spack_name in _MPI_SPACK_NAMES:
        if prefix in needle:
            return spack_name
    base = mpi_module.split("/")[0] if "/" in mpi_module else mpi_module
    return base or "mpi"


def _set_not_buildable(packages: Dict[str, Any], name: str) -> None:
    packages.setdefault(name, {})["buildable"] = False


def _add_module_external(packages: Dict[str, Any], name: str, spec: str, module: str) -> None:
    _set_not_buildable(packages, name)
    packages[name].setdefault("externals", []).append({"spec": spec, "modules": [module]})


def _cuda_arch_hint(compute_capability: str) -> str:
    """Convert NVIDIA compute capability '9.0' → Spack cuda_arch value '90'."""
    return compute_capability.replace(".", "") if compute_capability else ""


def classify_externals(profile: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build a Spack packages.yaml structure from a clusterinspector system profile.

    Returns a dict with keys 'packages' and 'gpu_arch_hint' (for use in comments).
    The output is a starter — extend with Linux system library externals via
    ``spack external find openssl cmake m4 git perl pkgconf``.
    """
    packages: Dict[str, Any] = {}

    system = profile.get("system") or {}
    vendor_substrate = profile.get("vendor_substrate") or {}
    ext_policy = profile.get("externals_policy") or {}
    hardware = profile.get("hardware") or {}
    gpus = hardware.get("gpus") or {}
    platform_class = str(system.get("platform_class") or "unknown")
    loaded_modules: List[str] = list(profile.get("modules", {}).get("loaded") or [])

    # GPU architecture hint (for Kokkos/RAJA cmake flags — not written to packages.yaml)
    gpu_vendor = str(gpus.get("vendor") or "").lower()
    compute_capability = str(gpus.get("compute_capability") or "").strip()
    if gpu_vendor == "nvidia":
        gpu_arch_hint = f"cuda_arch={_cuda_arch_hint(compute_capability)}" if compute_capability else ""
    elif gpu_vendor == "amd":
        gpu_arch_hint = f"amdgpu_target={compute_capability}" if compute_capability else ""
    else:
        gpu_arch_hint = ""

    # MPI — determine provider name early so 'all' section can be written first
    mpi_module = str(vendor_substrate.get("mpi_module") or "").strip()
    mpi_family = str(vendor_substrate.get("mpi_family") or "").strip()
    mpi_pkg_name = _mpi_spack_name(mpi_family, mpi_module) if mpi_module else ""

    # 'all' section first for readability
    if mpi_pkg_name:
        packages["all"] = {"providers": {"mpi": [mpi_pkg_name]}}

    # Mark every package in forbid_build as non-buildable
    for pkg in ext_policy.get("forbid_build") or []:
        _set_not_buildable(packages, str(pkg))

    # CUDA
    cuda_module = str(vendor_substrate.get("cuda_module") or "").strip()
    if cuda_module:
        version = _parse_version(cuda_module)
        spec = f"cuda@{version}" if version else "cuda"
        _add_module_external(packages, "cuda", spec, cuda_module)

    # ROCm — declare 'hip' (the Spack name for the ROCm SDK) plus the two
    # runtime sub-packages that Spack may resolve as dependencies.
    rocm_module = str(vendor_substrate.get("rocm_module") or "").strip()
    if rocm_module:
        version = _parse_version(rocm_module)
        spec = f"hip@{version}" if version else "hip"
        _add_module_external(packages, "hip", spec, rocm_module)
        for sub_pkg in ("rocm-opencl-runtime", "rocm-smi-lib"):
            _add_module_external(packages, sub_pkg, sub_pkg, rocm_module)

    # MPI
    if mpi_module and mpi_pkg_name:
        version = _parse_version(mpi_module)
        spec = f"{mpi_pkg_name}@{version}" if version else mpi_pkg_name
        _add_module_external(packages, mpi_pkg_name, spec, mpi_module)

    # CPE scientific libraries (Cray classes only)
    if platform_class.startswith("cray-"):
        for cpe_prefix, spack_name, variant_suffix in _CPE_LIBS:
            matched = next(
                (m for m in loaded_modules if m == cpe_prefix or m.startswith(cpe_prefix + "/")),
                None,
            )
            if matched:
                version = _parse_version(matched)
                base_spec = f"{spack_name}@{version}" if version else spack_name
                spec = (base_spec + variant_suffix).strip()
                _add_module_external(packages, spack_name, spec, matched)
            else:
                # Placeholder — not currently loaded but expected on this platform class
                _set_not_buildable(packages, spack_name)
                packages[spack_name].setdefault("externals", []).append({
                    "spec": spack_name,
                    "modules": [f"<{cpe_prefix}/VERSION>"],
                })

    return {"packages": packages, "gpu_arch_hint": gpu_arch_hint}
