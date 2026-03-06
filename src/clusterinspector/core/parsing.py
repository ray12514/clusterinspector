import re
from typing import Dict, List, Tuple


def lines(text: str) -> List[str]:
    return [ln for ln in (text or "").splitlines() if ln.strip()]


def parse_key_value_block(text: str) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for ln in lines(text):
        if ":" not in ln:
            continue
        k, v = ln.split(":", 1)
        out[k.strip().lower()] = v.strip()
    return out


def split_pipe_line(line: str, expected_parts: int) -> Tuple[bool, List[str]]:
    parts = [p.strip() for p in line.split("|")]
    if len(parts) != expected_parts:
        return False, []
    return True, parts


def regex_search(pattern: str, text: str) -> str:
    match = re.search(pattern, text or "")
    return match.group(1) if match else ""
