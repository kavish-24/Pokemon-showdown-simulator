from pathlib import Path

import yaml

from src.agent.models import SOP


def load_sop(path: Path) -> SOP:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    return SOP.model_validate(payload)


def load_selectors(path: Path) -> dict[str, list[str]]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise ValueError("Selector configuration must be a mapping.")
    return {
        str(name): [str(item) for item in values]
        for name, values in payload.items()
        if isinstance(values, list)
    }
