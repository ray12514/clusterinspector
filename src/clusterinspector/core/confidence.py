from typing import Iterable


def from_signal_count(count: int) -> str:
    if count >= 4:
        return "high"
    if count >= 2:
        return "medium"
    return "low"


def from_agreement(labels: Iterable[str]) -> str:
    values = [x for x in labels if x and x != "unknown"]
    if not values:
        return "low"
    unique = set(values)
    if len(unique) == 1 and len(values) >= 2:
        return "high"
    if len(unique) <= 2:
        return "medium"
    return "low"
