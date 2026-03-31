import argparse
import sys

from clusterinspector.fabric.cli import build_parser as build_fabric_parser
from clusterinspector.fabric.cli import run as run_fabric
from clusterinspector.generate.cli import build_parser as build_generate_parser
from clusterinspector.generate.cli import run as run_generate
from clusterinspector.profile.cli import build_parser as build_profile_parser
from clusterinspector.profile.cli import run as run_profile


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="clusterinspector", description="Cluster inspection toolkit")
    subparsers = parser.add_subparsers(dest="command", required=True)

    fabric_parser = subparsers.add_parser("fabric", help="Passive fabric discovery and diagnosis")
    build_fabric_parser(fabric_parser)

    profile_parser = subparsers.add_parser("profile", help="Platform profile collection")
    build_profile_parser(profile_parser)

    generate_parser = subparsers.add_parser("generate", help="Generate config artifacts from saved profiles")
    build_generate_parser(generate_parser)

    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "fabric":
        return run_fabric(args)
    if args.command == "profile":
        return run_profile(args)
    if args.command == "generate":
        return run_generate(args)

    parser.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
