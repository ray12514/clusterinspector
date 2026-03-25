import re
from typing import Dict, List, Set, Tuple

from clusterinspector.core.evidence import make_evidence
from clusterinspector.core.models import Evidence
from clusterinspector.core.runner import Runner
from clusterinspector.core.timeouts import Deadline


_NOISE_PROVIDER_TOKENS = {
    "provider",
    "providers",
    "version",
    "fabric",
    "domain",
    "type",
    "protocol",
    "endpoint",
}


def _provider_tokens(value: str) -> List[str]:
    tokens: List[str] = []
    for raw in re.split(r"[\s,;/]+", (value or "").lower()):
        token = raw.strip().strip(":").strip("[]()")
        if not token or token in _NOISE_PROVIDER_TOKENS:
            continue
        tokens.append(token)
    return tokens


def _providers_from_list(stdout: str) -> List[str]:
    providers: Set[str] = set()
    for line in (stdout or "").splitlines():
        item = line.strip()
        if not item:
            continue

        lower = item.lower()
        if lower.startswith("provider") and ":" in item:
            for token in _provider_tokens(item.split(":", 1)[1]):
                providers.add(token)
            continue

        token = item.split()[0].strip().rstrip(":")
        for normalized in _provider_tokens(token):
            providers.add(normalized)
    return sorted(providers)


def _providers_from_full(stdout: str) -> List[str]:
    providers: Set[str] = set()
    for raw in (stdout or "").splitlines():
        line = raw.strip()
        if not line:
            continue

        lower = line.lower()
        if lower.startswith("provider") and ":" in line:
            value = line.split(":", 1)[1].strip()
            for token in _provider_tokens(value):
                providers.add(token)
            continue

        if re.match(r"^[a-z0-9_+.-]+:\s*$", lower):
            for token in _provider_tokens(lower.split(":", 1)[0]):
                providers.add(token)

    return sorted(providers)


def probe_libfabric(
    *,
    runner: Runner,
    host: str,
    deadline: Deadline,
    command_timeout_s: int,
) -> Tuple[Dict[str, object], List[Evidence]]:
    if deadline.expired():
        raise TimeoutError("node deadline expired before libfabric probe")

    cmd_timeout = min(command_timeout_s, deadline.remaining_seconds())
    evidence: List[Evidence] = []

    fi_list = runner.run(host, ["fi_info", "-l"], timeout_s=cmd_timeout)
    fi_full = runner.run(host, ["fi_info"], timeout_s=cmd_timeout)

    providers = set(_providers_from_list(fi_list.stdout))
    providers.update(_providers_from_full(fi_full.stdout))
    providers_sorted = sorted(providers)

    fast_markers = {"verbs", "cxi", "psm2", "psm3", "opx", "efa", "gni", "ucx"}
    has_fast_provider = any(p in fast_markers for p in providers_sorted)

    if providers_sorted:
        evidence.append(
            make_evidence(
                code="libfabric_providers_visible",
                message=f"Visible libfabric providers: {', '.join(providers_sorted)}",
                source="libfabric",
                confidence="high",
            )
        )
    elif fi_list.returncode == 127 and fi_full.returncode == 127:
        evidence.append(
            make_evidence(
                code="fi_info_unavailable",
                message="fi_info not available on node",
                source="libfabric",
                confidence="medium",
            )
        )
    elif fi_list.returncode != 0 or fi_full.returncode != 0:
        evidence.append(
            make_evidence(
                code="fi_info_error",
                message="fi_info returned an error before provider parsing",
                source="libfabric",
                confidence="medium",
                data={
                    "fi_info_l_returncode": fi_list.returncode,
                    "fi_info_returncode": fi_full.returncode,
                    "fi_info_l_stderr": fi_list.stderr.strip(),
                    "fi_info_stderr": fi_full.stderr.strip(),
                },
            )
        )
    else:
        evidence.append(
            make_evidence(
                code="libfabric_no_provider_data",
                message="fi_info ran without provider results",
                source="libfabric",
                confidence="low",
            )
        )

    return {
        "providers": providers_sorted,
        "provider_count": len(providers_sorted),
        "has_fast_provider": has_fast_provider,
        "fi_info_l_returncode": fi_list.returncode,
        "fi_info_returncode": fi_full.returncode,
    }, evidence
