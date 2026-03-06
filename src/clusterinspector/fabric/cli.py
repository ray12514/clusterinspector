import argparse

from clusterinspector.fabric.orchestrator import scan_fabric
from clusterinspector.fabric.output.human import render_human
from clusterinspector.fabric.output.jsonout import render_json


def build_parser(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    parser.add_argument("--local", action="store_true", help="Scan current host only")
    parser.add_argument("--nodes", default="", help="Comma-separated hostnames")
    parser.add_argument("--hosts-file", default="", help="Path to hosts file")
    parser.add_argument("--scheduler", choices=["none", "pbs", "slurm"], default="none")
    parser.add_argument("--summary", action="store_true", help="Print fleet summary")
    parser.add_argument("--diagnose", action="store_true", help="Include diagnosis codes")
    parser.add_argument("--evidence", action="store_true", help="Include evidence in human output")
    parser.add_argument("--format", choices=["human", "json"], default="human")
    parser.add_argument("--include-gpu", action="store_true", help="Reserved for GPU path hints")
    parser.add_argument(
        "--passive-only",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Passive read-only mode",
    )
    parser.add_argument("--workers", type=int, default=16, help="SSH fanout workers")
    parser.add_argument("--command-timeout", type=int, default=8, help="Per-command timeout seconds")
    parser.add_argument("--node-timeout", type=int, default=45, help="Per-node timeout seconds")
    return parser


def run(args: argparse.Namespace) -> int:
    fleet = scan_fabric(args)
    if args.format == "json":
        print(render_json(fleet, include_raw=False))
    else:
        print(render_human(fleet, include_summary=args.summary, include_diagnoses=args.diagnose, include_evidence=args.evidence))

    node_errors = sum(1 for n in fleet.nodes if not n.ok)
    return 2 if node_errors else 0
