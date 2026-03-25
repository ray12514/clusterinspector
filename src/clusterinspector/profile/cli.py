import argparse
import os
import re
from typing import Dict, List

from clusterinspector.profile.orchestrator import collect_profile
from clusterinspector.profile.output.human import render_human
from clusterinspector.profile.output.jsonout import render_json
from clusterinspector.profile.output.yamlout import render_yaml


def _slug(value: str, default: str = "unknown") -> str:
    text = (value or "").strip().lower()
    if not text:
        return default
    text = text.replace("_", "-").replace("/", "-").replace(":", "-")
    text = re.sub(r"\s+", "-", text)
    text = re.sub(r"[^a-z0-9.-]+", "-", text)
    text = re.sub(r"-{2,}", "-", text).strip("-.")
    return text or default


def _profiles_from_payload(payload: Dict[str, object]) -> List[Dict[str, object]]:
    profiles = payload.get("profiles")
    if isinstance(profiles, list):
        return profiles
    return [payload]


def _infer_context_name(profile: Dict[str, object], override: str = "") -> str:
    if override:
        return _slug(override)

    active_context = profile.get("modules", {}).get("active_context", {})
    prgenv = _slug(active_context.get("prgenv_module", ""), "")
    gpu_runtime = _slug(active_context.get("gpu_runtime_module", ""), "")
    mpi_module = _slug(active_context.get("mpi_module", ""), "")
    wrapper_family = _slug(active_context.get("compiler_wrapper_family", ""), "")
    environment_model = _slug(profile.get("system", {}).get("environment_model", ""), "")

    if prgenv and gpu_runtime:
        return f"{prgenv}-{gpu_runtime}"
    if prgenv:
        return prgenv
    if mpi_module and gpu_runtime:
        return f"{mpi_module}-{gpu_runtime}"
    if gpu_runtime:
        return gpu_runtime
    if mpi_module:
        return mpi_module
    if wrapper_family and wrapper_family != "unknown":
        return wrapper_family
    if environment_model and environment_model != "unknown":
        return environment_model
    return "default-shell"


def _apply_context_names(payload: Dict[str, object], override: str = "") -> None:
    for profile in _profiles_from_payload(payload):
        modules = profile.setdefault("modules", {})
        active_context = modules.setdefault("active_context", {})
        active_context["context_name"] = _infer_context_name(profile, override=override)


def _apply_system_overrides(payload: Dict[str, object], system_name: str = "", site_name: str = "") -> None:
    for profile in _profiles_from_payload(payload):
        system = profile.setdefault("system", {})
        if system_name:
            system["name"] = system_name
        if site_name:
            system["site"] = site_name


def _render_payload(payload: Dict[str, object], output_format: str) -> str:
    if output_format == "json":
        return render_json(payload)
    if output_format == "yaml":
        return render_yaml(payload)
    return render_human(payload)


def _output_extension(output_format: str) -> str:
    return {"json": "json", "yaml": "yaml", "human": "txt"}[output_format]


def _artifact_filename(profile: Dict[str, object], output_format: str) -> str:
    system = profile.get("system", {})
    active_context = profile.get("modules", {}).get("active_context", {})
    node_role = _slug(system.get("node_role", "unknown"))
    platform_class = _slug(system.get("platform_class", "unknown"))
    context_name = _slug(active_context.get("context_name", ""), "default-shell")
    return f"{node_role}--{platform_class}--{context_name}.{_output_extension(output_format)}"


def _write_single_output(path: str, text: str) -> str:
    directory = os.path.dirname(path)
    if directory:
        os.makedirs(directory, exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(text)
        if not text.endswith("\n"):
            handle.write("\n")
    return path


def _dedupe_path(path: str, used_paths: set[str]) -> str:
    if path not in used_paths:
        used_paths.add(path)
        return path

    root, ext = os.path.splitext(path)
    index = 2
    candidate = f"{root}-{index}{ext}"
    while candidate in used_paths:
        index += 1
        candidate = f"{root}-{index}{ext}"
    used_paths.add(candidate)
    return candidate


def _write_output(payload: Dict[str, object], output_format: str, output_path: str = "", output_dir: str = "") -> List[str]:
    text = _render_payload(payload, output_format)
    if output_path:
        return [_write_single_output(output_path, text)]

    if not output_dir:
        return []

    os.makedirs(output_dir, exist_ok=True)
    written: List[str] = []
    used_paths: set[str] = set()
    for profile in _profiles_from_payload(payload):
        filename = _artifact_filename(profile, output_format)
        target_path = _dedupe_path(os.path.join(output_dir, filename), used_paths)
        rendered = _render_payload(profile, output_format)
        written.append(_write_single_output(target_path, rendered))
    return written


def build_parser(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    parser.add_argument("--local", action="store_true", help="Profile current host")
    parser.add_argument("--nodes", default="", help="Comma-separated hostnames")
    parser.add_argument("--format", choices=["human", "yaml", "json"], default="human")
    parser.add_argument("--output", default="", help="Write rendered output to a file")
    parser.add_argument("--output-dir", default="", help="Write one artifact per profile into a directory")
    parser.add_argument("--context-name", default="", help="Override the active context name used in artifact naming")
    parser.add_argument("--system-name", default="", help="Override the emitted system name")
    parser.add_argument("--site", default="", help="Override the emitted site name")
    parser.add_argument("--include-gpu", action="store_true")
    parser.add_argument("--include-mpi", action="store_true")
    parser.add_argument("--include-modules", action="store_true")

    subparsers = parser.add_subparsers(dest="profile_action")
    submit = subparsers.add_parser("submit", help="Submit batch profiling job")
    submit.add_argument("--scheduler", choices=["pbs", "slurm"], required=True)
    submit.add_argument("--partition", default="")
    submit.add_argument("--queue", default="")
    submit.add_argument("--output", dest="submit_output", default="profiles/")
    return parser


def run(args: argparse.Namespace) -> int:
    if getattr(args, "profile_action", "") == "submit":
        print("profile submit is scaffolded and not implemented yet")
        return 2
    if getattr(args, "output", "") and getattr(args, "output_dir", ""):
        print("profile collection failed: use either --output or --output-dir, not both")
        return 2

    try:
        payload = collect_profile(args)
    except Exception as exc:
        print(f"profile collection failed: {exc}")
        return 2

    _apply_system_overrides(
        payload,
        system_name=getattr(args, "system_name", ""),
        site_name=getattr(args, "site", ""),
    )
    _apply_context_names(payload, override=getattr(args, "context_name", ""))
    written_paths = _write_output(
        payload,
        args.format,
        output_path=getattr(args, "output", ""),
        output_dir=getattr(args, "output_dir", ""),
    )
    if written_paths:
        print("\n".join(written_paths))
        return 0

    print(_render_payload(payload, args.format))
    return 0
