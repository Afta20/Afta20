"""Configuration loading and XML/SVG escaping helpers using Python stdlib."""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any


def load_profile_config(config_path: Path) -> dict[str, Any]:
    """Load profile.config.toml using Python's built-in tomllib."""
    with config_path.open("rb") as handle:
        data = tomllib.load(handle)

    required_sections = ("profile", "contacts", "theme", "projects")
    for section in required_sections:
        if section not in data:
            raise ValueError(f"Missing required [{section}] section in {config_path}")

    return data


def escape_xml(text: Any) -> str:
    """Escape dynamic text safely for SVG/XML interpolation."""
    value = str(text)
    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )
