from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass
class CommandResult:
    host: str
    command: List[str]
    returncode: int
    stdout: str
    stderr: str
    started_at: str
    finished_at: str
    duration_s: float
    timeout: bool = False
    error: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Evidence:
    code: str
    message: str
    source: str
    confidence: str = "low"
    data: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class InterfaceRecord:
    name: str
    operstate: str = "unknown"
    mac: str = ""
    device_path: str = ""
    is_up: bool = False
    driver: str = ""
    bus_info: str = ""
    firmware: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class NodeReport:
    hostname: str
    ok: bool = True
    error: str = ""
    primary_fabric: str = "unknown"
    secondary_fabrics: List[str] = field(default_factory=list)
    management_fabric: str = "unknown"
    likely_hpc_fabric: str = "unknown"
    health: str = "unknown"
    confidence: str = "low"
    gpu_network_path: str = "unknown"
    gpu_vendor: str = "unknown"
    gpu_count: int = 0
    diagnoses: List[str] = field(default_factory=list)
    interfaces: List[InterfaceRecord] = field(default_factory=list)
    evidence: List[Evidence] = field(default_factory=list)
    raw: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self, include_raw: bool = True) -> Dict[str, Any]:
        data = {
            "hostname": self.hostname,
            "ok": self.ok,
            "error": self.error,
            "primary_fabric": self.primary_fabric,
            "secondary_fabrics": self.secondary_fabrics,
            "management_fabric": self.management_fabric,
            "likely_hpc_fabric": self.likely_hpc_fabric,
            "health": self.health,
            "confidence": self.confidence,
            "gpu_network_path": self.gpu_network_path,
            "gpu_vendor": self.gpu_vendor,
            "gpu_count": self.gpu_count,
            "diagnoses": self.diagnoses,
            "interfaces": [i.to_dict() for i in self.interfaces],
            "evidence": [e.to_dict() for e in self.evidence],
        }
        if include_raw:
            data["raw"] = self.raw
        return data


@dataclass
class FleetReport:
    nodes: List[NodeReport]
    generated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    summary: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self, include_raw: bool = True) -> Dict[str, Any]:
        return {
            "generated_at": self.generated_at,
            "summary": self.summary,
            "nodes": [n.to_dict(include_raw=include_raw) for n in self.nodes],
        }
