import argparse


def build_parser(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    parser.add_argument("--local", action="store_true", help="Profile current host")
    parser.add_argument("--nodes", default="", help="Comma-separated hostnames")
    parser.add_argument("--format", choices=["human", "yaml", "json"], default="human")
    parser.add_argument("--include-gpu", action="store_true")
    parser.add_argument("--include-mpi", action="store_true")
    parser.add_argument("--include-modules", action="store_true")

    subparsers = parser.add_subparsers(dest="profile_action")
    submit = subparsers.add_parser("submit", help="Submit batch profiling job")
    submit.add_argument("--scheduler", choices=["pbs", "slurm"], required=True)
    submit.add_argument("--partition", default="")
    submit.add_argument("--queue", default="")
    submit.add_argument("--output", default="profiles/")
    return parser


def run(args: argparse.Namespace) -> int:
    if getattr(args, "profile_action", "") == "submit":
        print("profile submit is scaffolded and not implemented yet")
        return 2
    print("profile collection is scaffolded and not implemented yet")
    return 2
