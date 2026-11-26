"""GitHub Primer color tokens and Editorial Bento palette definitions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ThemePalette:
    mode: str
    canvas: str
    surface: str
    surface_alt: str
    text_primary: str
    text_muted: str
    border: str
    border_subtle: str
    accent: str
    accent_soft: str
    success: str
    success_soft: str
    warning: str
    danger: str
    grid_dot: str
    bar_track: str


def get_palette(mode: str, theme_cfg: dict[str, Any] | None = None) -> ThemePalette:
    """Build Primer-aligned palette for 'dark' or 'light' mode."""
    cfg = theme_cfg or {}
    if mode == "dark":
        accent = str(cfg.get("accent_dark", "#2f81f7"))
        success = str(cfg.get("secondary_dark", "#3fb950"))
        return ThemePalette(
            mode="dark",
            canvas="#0d1117",
            surface="#161b22",
            surface_alt="#1c2128",
            text_primary="#e6edf3",
            text_muted="#848d97",
            border="#30363d",
            border_subtle="#21262d",
            accent=accent,
            accent_soft="#13233a",
            success=success,
            success_soft="#122b1e",
            warning="#d29922",
            danger="#f85149",
            grid_dot="#262c36",
            bar_track="#21262d",
        )
    if mode == "light":
        accent = str(cfg.get("accent_light", "#0969da"))
        success = str(cfg.get("secondary_light", "#1a7f37"))
        return ThemePalette(
            mode="light",
            canvas="#ffffff",
            surface="#f6f8fa",
            surface_alt="#eaeef2",
            text_primary="#1f2328",
            text_muted="#636c76",
            border="#d0d7de",
            border_subtle="#e5e9ef",
            accent=accent,
            accent_soft="#ddf4ff",
            success=success,
            success_soft="#dafbe1",
            warning="#9a6700",
            danger="#d1242f",
            grid_dot="#d8dee4",
            bar_track="#eaeef2",
        )
    raise ValueError(f"Unsupported theme mode: {mode}")
