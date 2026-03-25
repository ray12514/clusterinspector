from typing import Any, List


def _scalar(value: Any) -> str:
    if value is None:
        return "null"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, (int, float)):
        return str(value)
    text = str(value)
    if text == "" or any(ch in text for ch in [":", "#", "\n"]) or text.strip() != text:
        escaped = text.replace('"', '\\"')
        return f'"{escaped}"'
    return text


def _render(value: Any, indent: int = 0) -> List[str]:
    pad = " " * indent
    if isinstance(value, dict):
        if not value:
            return [f"{pad}{{}}"]
        lines: List[str] = []
        for key, item in value.items():
            if isinstance(item, dict) and not item:
                lines.append(f"{pad}{key}: {{}}")
            elif isinstance(item, list) and not item:
                lines.append(f"{pad}{key}: []")
            elif isinstance(item, (dict, list)):
                lines.append(f"{pad}{key}:")
                lines.extend(_render(item, indent + 2))
            else:
                lines.append(f"{pad}{key}: {_scalar(item)}")
        return lines
    if isinstance(value, list):
        if not value:
            return [f"{pad}[]"]
        lines = []
        for item in value:
            if isinstance(item, (dict, list)):
                lines.append(f"{pad}-")
                lines.extend(_render(item, indent + 2))
            else:
                lines.append(f"{pad}- {_scalar(item)}")
        return lines
    return [f"{pad}{_scalar(value)}"]


def render_yaml(profile: dict) -> str:
    return "\n".join(_render(profile))
