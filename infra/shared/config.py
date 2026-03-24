"""Read and write richmond.yaml config files."""
from pathlib import Path
from typing import Any

import yaml


def resolve_config_path() -> Path:
    """Resolve the path to richmond.yaml from the current working directory.

    Pulumi always runs __main__.py with cwd set to the stack directory
    (e.g. infra/vercel/), so richmond.yaml is two levels up at the repo root.
    Using cwd instead of __file__ avoids the installed-package path problem
    where __file__ resolves into .venv/lib/pythonX.Y/site-packages/.
    """
    return Path.cwd().parents[1] / "richmond.yaml"


def load_richmond_config(path: str | Path | None = None) -> dict[str, Any]:
    """Load and parse richmond.yaml.

    Args:
        path: Explicit path to richmond.yaml. If None, resolves automatically.

    Returns:
        Parsed YAML as a dict.

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    config_path = Path(path) if path else resolve_config_path()
    if not config_path.exists():
        raise FileNotFoundError(f"richmond.yaml not found at {config_path}")
    with open(config_path) as f:
        return yaml.safe_load(f) or {}


def _deep_merge(base: dict, updates: dict) -> dict:
    """Recursively merge updates into base dict."""
    for key, value in updates.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value
    return base


def update_richmond_config(path: str | Path | None = None, updates: dict | None = None) -> None:
    """Merge updates into richmond.yaml, preserving existing keys.

    Args:
        path: Explicit path to richmond.yaml. If None, resolves automatically.
        updates: Dict of keys to merge into the config.
    """
    if updates is None:
        return
    config_path = Path(path) if path else resolve_config_path()
    config = load_richmond_config(config_path)
    _deep_merge(config, updates)
    with open(config_path, "w") as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)
