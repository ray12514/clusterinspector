def render_markdown(profile: dict) -> str:
    lines = ["# Profile", ""]
    for key, value in profile.items():
        lines.append(f"- {key}: {value}")
    return "\n".join(lines)
