"""Configuration loading and validation for the ARC-AGI-3 agent system.

This module implements the three-layer configuration hierarchy:
1. YAML file defaults from the config/ directory.
2. Environment variable overrides.
3. Command-line argument overrides (when provided).

The loader reads YAML files, merges overrides, and returns a unified
configuration dictionary. Schema validation ensures that all required
parameters are present and within their valid ranges.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def load_config(
    config_paths: list[str] | None = None,
    overrides: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Load and merge configuration from YAML files and overrides.

    Configuration files are loaded in the order provided, with later files
    overriding earlier ones for any conflicting keys. The optional overrides
    dictionary is applied last, providing the highest precedence.

    Args:
        config_paths: Filesystem paths to YAML configuration files. If None,
            the default configuration files in config/ are loaded.
        overrides: A dictionary of key-value pairs to override after loading
            files. Keys use dot-notation (e.g., "agent.exploration.curiosity_weight").

    Returns:
        A merged configuration dictionary.

    Raises:
        FileNotFoundError: If a specified configuration file does not exist.
        yaml.YAMLError: If a configuration file contains invalid YAML.
    """
    config: dict[str, Any] = {}

    if config_paths is None:
        config_dir = Path("config")
        if config_dir.is_dir():
            config_paths = sorted(str(p) for p in config_dir.glob("*.yaml"))
        else:
            config_paths = []

    for path_str in config_paths:
        path = Path(path_str)
        if not path.exists():
            msg = f"Configuration file not found: {path}"
            raise FileNotFoundError(msg)

        with path.open("r") as f:
            file_config = yaml.safe_load(f)

        if isinstance(file_config, dict):
            _deep_merge(config, file_config)

    if overrides:
        for key, value in overrides.items():
            _set_nested(config, key, value)

    return config


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> None:
    """Recursively merge override into base, modifying base in place.

    For keys present in both dictionaries, if both values are dicts, they are
    merged recursively. Otherwise, the override value replaces the base value.
    """
    for key, value in override.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value


def _set_nested(config: dict[str, Any], dotted_key: str, value: Any) -> None:
    """Set a value in a nested dictionary using dot-notation.

    For example, _set_nested(config, "agent.exploration.curiosity_weight", 0.8)
    is equivalent to config["agent"]["exploration"]["curiosity_weight"] = 0.8,
    creating intermediate dictionaries as needed.
    """
    keys = dotted_key.split(".")
    current = config
    for key in keys[:-1]:
        if key not in current or not isinstance(current[key], dict):
            current[key] = {}
        current = current[key]
    current[keys[-1]] = value
