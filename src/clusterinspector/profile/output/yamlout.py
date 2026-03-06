def render_yaml(profile: dict) -> str:
    lines = []
    for key, value in profile.items():
        lines.append(f"{key}: {value}")
    return "\n".join(lines)
