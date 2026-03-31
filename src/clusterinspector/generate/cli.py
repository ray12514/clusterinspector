"""
clusterinspector generate — offline generation from saved profile artifacts.

Usage:
    clusterinspector generate spack-packages profile.json
    clusterinspector profile --local --format json | clusterinspector generate spack-packages -
"""

import argparse
import json
import sys
from typing import Dict, Any

from clusterinspector.profile.output.spackpackages import render_spack_packages


def _load_json(path: str) -> Dict[str, Any]:
    if path == "-":
        return json.load(sys.stdin)
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def build_parser(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    subparsers = parser.add_subparsers(dest="generate_action", required=True)

    sp = subparsers.add_parser(
        "spack-packages",
        help="Generate a Spack packages.yaml starter from a JSON profile",
    )
    sp.add_argument(
        "profile",
        metavar="PROFILE",
        help="Path to a JSON profile file produced by 'clusterinspector profile --format json', or '-' to read from stdin",
    )
    sp.add_argument(
        "--output",
        default="",
        help="Write output to a file instead of stdout",
    )
    return parser


def run(args: argparse.Namespace) -> int:
    if args.generate_action == "spack-packages":
        try:
            payload = _load_json(args.profile)
        except (OSError, json.JSONDecodeError) as exc:
            print(f"generate spack-packages failed: {exc}", file=sys.stderr)
            return 2

        text = render_spack_packages(payload)

        output_path = getattr(args, "output", "")
        if output_path:
            try:
                with open(output_path, "w", encoding="utf-8") as fh:
                    fh.write(text)
                    if not text.endswith("\n"):
                        fh.write("\n")
                print(output_path)
            except OSError as exc:
                print(f"generate spack-packages failed: {exc}", file=sys.stderr)
                return 2
        else:
            print(text)

        return 0

    return 2
