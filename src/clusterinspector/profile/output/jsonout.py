import json


def render_json(profile: dict) -> str:
    return json.dumps(profile, indent=2, sort_keys=True)
