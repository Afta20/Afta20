"""Shared SVG primitives, layout helpers, and sandbox-safe CSS scaffolding."""

from __future__ import annotations

import textwrap

from src.config_loader import escape_xml
from src.svg.theme import ThemePalette

SYSTEM_SANS = (
    "-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif"
)
SYSTEM_MONO = (
    "ui-monospace, SFMono-Regular, SF Mono, Menlo, Consolas, 'Liberation Mono', monospace"
)


def wrap_text_lines(text: str, max_chars: int, max_lines: int) -> list[str]:
    """Wrap text cleanly into bounded lines with ellipsis overflow protection."""
    words = " ".join(text.split())
    lines = textwrap.wrap(words, width=max_chars, break_long_words=True)
    if len(lines) <= max_lines:
        return lines
    clipped = lines[:max_lines]
    last = clipped[-1]
    if len(last) > max_chars - 3:
        last = last[: max_chars - 3].rstrip()
    clipped[-1] = f"{last}..."
    return clipped


def svg_document(
    width: int,
    height: int,
    title: str,
    desc: str,
    style_css: str,
    body: str,
    defs_extra: str = "",
) -> str:
    """Wrap pure SVG primitives in a sandbox-compliant, accessible root SVG."""
    reduced_motion_css = (
        "@media (prefers-reduced-motion: reduce) {\n"
        "      *, *::before, *::after { animation: none !important; transition: none !important; }\n"
        "    }"
    )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {width} {height}" width="{width}" height="{height}" '
        f'role="img" aria-labelledby="svg-title svg-desc">\n'
        f'  <title id="svg-title">{escape_xml(title)}</title>\n'
        f'  <desc id="svg-desc">{escape_xml(desc)}</desc>\n'
        f'  <defs>\n'
        f'    <style>\n'
        f'    .font-sans {{ font-family: {SYSTEM_SANS}; }}\n'
        f'    .font-mono {{ font-family: {SYSTEM_MONO}; }}\n'
        f'{style_css}\n'
        f'    {reduced_motion_css}\n'
        f'    </style>\n'
        f'{defs_extra}'
        f'  </defs>\n'
        f'{body}'
        f'</svg>\n'
    )


def render_bento_panel(
    x: int,
    y: int,
    w: int,
    h: int,
    palette: ThemePalette,
    radius: int = 10,
    fill: str | None = None,
) -> str:
    """Render a crisp GitHub Primer Bento card rectangle."""
    panel_fill = fill or palette.surface
    return (
        f'  <rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" '
        f'fill="{panel_fill}" stroke="{palette.border}" stroke-width="1"/>\n'
    )


def render_pill(
    x: int,
    y: int,
    label: str,
    fg: str,
    bg: str,
    border: str,
    font_size: int = 11,
    mono: bool = True,
    pad_x: int = 10,
    height: int = 22,
) -> tuple[str, int]:
    """Render a pill badge and return (svg_markup, computed_width)."""
    char_w = 6.6 if mono else 6.2
    width = max(44, round(len(label) * char_w + pad_x * 2))
    font_cls = "font-mono" if mono else "font-sans"
    text_y = y + (height / 2) + (font_size * 0.35)
    markup = (
        f'  <g>\n'
        f'    <rect x="{x}" y="{y}" width="{width}" height="{height}" rx="{height // 2}" '
        f'fill="{bg}" stroke="{border}" stroke-width="1"/>\n'
        f'    <text x="{x + width / 2:.1f}" y="{text_y:.1f}" text-anchor="middle" '
        f'class="{font_cls}" font-size="{font_size}" font-weight="600" fill="{fg}">'
        f'{escape_xml(label)}</text>\n'
        f'  </g>\n'
    )
    return markup, width
