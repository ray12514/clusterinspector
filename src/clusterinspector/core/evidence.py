from typing import Any, Dict, List, Optional

from .models import Evidence


def make_evidence(
    *,
    code: str,
    message: str,
    source: str,
    confidence: str = "low",
    data: Optional[Dict[str, Any]] = None,
) -> Evidence:
    return Evidence(
        code=code,
        message=message,
        source=source,
        confidence=confidence,
        data=data or {},
    )


def append_evidence(target: List[Evidence], item: Evidence) -> None:
    target.append(item)
