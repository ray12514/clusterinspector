from collections import Counter
from typing import List

from clusterinspector.core.host_resolver import resolve_hosts
from clusterinspector.core.local import LocalRunner
from clusterinspector.core.models import FleetReport, NodeReport
from clusterinspector.core.ssh import SSHRunner
from clusterinspector.core.timeouts import Deadline
from clusterinspector.fabric.classify.fabrics import classify_fabrics
from clusterinspector.fabric.classify.health import classify_health
from clusterinspector.fabric.classify.impact import classify_impact
from clusterinspector.fabric.probes.drivers import probe_drivers
from clusterinspector.fabric.probes.interfaces import probe_interfaces
from clusterinspector.fabric.probes.libfabric import probe_libfabric
from clusterinspector.fabric.probes.pci import probe_pci
from clusterinspector.fabric.probes.rdma import probe_rdma


def _summarize(nodes: List[NodeReport]) -> dict:
    by_health = Counter(n.health for n in nodes)
    by_fabric = Counter(n.primary_fabric for n in nodes)
    return {
        "nodes_total": len(nodes),
        "nodes_ok": sum(1 for n in nodes if n.ok),
        "nodes_error": sum(1 for n in nodes if not n.ok),
        "by_health": dict(sorted(by_health.items())),
        "by_primary_fabric": dict(sorted(by_fabric.items())),
    }


def scan_fabric(args) -> FleetReport:
    hosts = resolve_hosts(
        local=bool(args.local),
        nodes=args.nodes or None,
        hosts_file=args.hosts_file or None,
        scheduler=args.scheduler or "none",
    )
    if not hosts:
        return FleetReport(nodes=[], summary={"nodes_total": 0, "error": "no hosts resolved"})

    runner = LocalRunner() if args.local else SSHRunner(max_workers=args.workers)
    reports: List[NodeReport] = []

    for host in hosts:
        deadline = Deadline.from_seconds(args.node_timeout)
        node = NodeReport(hostname=host)
        try:
            interfaces, intf_evidence, intf_raw = probe_interfaces(
                runner=runner,
                host=host,
                deadline=deadline,
                command_timeout_s=args.command_timeout,
            )
            node.interfaces = interfaces
            node.evidence.extend(intf_evidence)
            node.raw["interfaces"] = intf_raw

            pci_data, pci_evidence = probe_pci(
                runner=runner,
                host=host,
                deadline=deadline,
                command_timeout_s=args.command_timeout,
            )
            node.evidence.extend(pci_evidence)
            node.raw["pci"] = pci_data

            driver_data, driver_evidence = probe_drivers(
                runner=runner,
                host=host,
                interfaces=interfaces,
                deadline=deadline,
                command_timeout_s=args.command_timeout,
            )
            node.evidence.extend(driver_evidence)
            node.raw["drivers"] = driver_data

            rdma_data, rdma_evidence = probe_rdma(
                runner=runner,
                host=host,
                deadline=deadline,
                command_timeout_s=args.command_timeout,
            )
            node.evidence.extend(rdma_evidence)
            node.raw["rdma"] = rdma_data

            libfabric_data, libfabric_evidence = probe_libfabric(
                runner=runner,
                host=host,
                deadline=deadline,
                command_timeout_s=args.command_timeout,
            )
            node.evidence.extend(libfabric_evidence)
            node.raw["libfabric"] = libfabric_data

            classify_fabrics(node)
            classify_health(node)
            classify_impact(node)
        except Exception as exc:
            node.ok = False
            node.error = str(exc)
            if not node.diagnoses:
                node.diagnoses.append("node_probe_failed")

        reports.append(node)

    return FleetReport(nodes=reports, summary=_summarize(reports))
