"""Clickable Editorial Bento Featured Project Card SVG generator (405x198)."""

from __future__ import annotations

from typing import Any

from src.config_loader import escape_xml
from src.svg.primitives import render_pill, svg_document, wrap_text_lines
from src.svg.theme import ThemePalette, get_palette


def _render_motif(motif: str, cx: int, cy: int, palette: ThemePalette) -> str:
    """Render a minimal vector schematic icon for each project domain."""
    if motif == "radar":
        return (
            f'  <g>\n'
            f'    <circle cx="{cx}" cy="{cy}" r="15" fill="{palette.accent_soft}" stroke="{palette.border}" stroke-width="1"/>\n'
            f'    <circle cx="{cx}" cy="{cy}" r="9" fill="none" stroke="{palette.accent}" stroke-width="1" opacity="0.65" class="motif-pulse"/>\n'
            f'    <line x1="{cx}" y1="{cy}" x2="{cx + 8}" y2="{cy - 7}" stroke="{palette.accent}" stroke-width="1.8" stroke-linecap="round"/>\n'
            f'    <circle cx="{cx}" cy="{cy}" r="2.3" fill="{palette.success}"/>\n'
            f'  </g>\n'
        )
    if motif == "shield":
        return (
            f'  <g>\n'
            f'    <circle cx="{cx}" cy="{cy}" r="15" fill="{palette.success_soft}" stroke="{palette.border}" stroke-width="1"/>\n'
            f'    <path d="M {cx} {cy - 9} L {cx + 8} {cy - 5} V {cy + 1} C {cx + 8} {cy + 6} {cx} {cy + 10} {cx} {cy + 10} '
            f'C {cx} {cy + 10} {cx - 8} {cy + 6} {cx - 8} {cy + 1} V {cy - 5} Z" '
            f'fill="none" stroke="{palette.success}" stroke-width="1.6" class="motif-pulse"/>\n'
            f'    <path d="M {cx - 3} {cy + 1} L {cx - 0.5} {cy + 3.5} L {cx + 4} {cy - 2}" '
            f'fill="none" stroke="{palette.success}" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>\n'
            f'  </g>\n'
        )
    if motif == "scan":
        return (
            f'  <g>\n'
            f'    <circle cx="{cx}" cy="{cy}" r="15" fill="{palette.accent_soft}" stroke="{palette.border}" stroke-width="1"/>\n'
            f'    <path d="M {cx - 8} {cy - 4} V {cy - 8} H {cx - 4} M {cx + 4} {cy - 8} H {cx + 8} V {cy - 4} '
            f'M {cx - 8} {cy + 4} V {cy + 8} H {cx - 4} M {cx + 4} {cy + 8} H {cx + 8} V {cy + 4}" '
            f'fill="none" stroke="{palette.accent}" stroke-width="1.6" stroke-linecap="round"/>\n'
            f'    <line x1="{cx - 7}" y1="{cy}" x2="{cx + 7}" y2="{cy}" stroke="{palette.warning}" stroke-width="1.6" class="motif-pulse"/>\n'
            f'  </g>\n'
        )
    # Default: commerce / stack grid motif
    return (
        f'  <g>\n'
        f'    <circle cx="{cx}" cy="{cy}" r="15" fill="{palette.surface_alt}" stroke="{palette.border}" stroke-width="1"/>\n'
        f'    <rect x="{cx - 7}" y="{cy - 7}" width="6" height="6" rx="1.5" fill="{palette.accent}" class="motif-pulse"/>\n'
        f'    <rect x="{cx + 1}" y="{cy - 7}" width="6" height="6" rx="1.5" fill="{palette.success}"/>\n'
        f'    <rect x="{cx - 7}" y="{cy + 1}" width="6" height="6" rx="1.5" fill="{palette.warning}"/>\n'
        f'    <rect x="{cx + 1}" y="{cy + 1}" width="6" height="6" rx="1.5" fill="{palette.accent}"/>\n'
        f'  </g>\n'
    )


def render_project_card_svg(
    project: dict[str, Any],
    theme_cfg: dict[str, Any],
    mode: str,
    index: int = 0,
) -> str:
    """Render 405x198 Bento Project Card SVG designed for 2-column README layout."""
    palette = get_palette(mode, theme_cfg)
    loop_s = int(theme_cfg.get("loop_seconds", 24))

    name = str(project.get("name", "Project"))
    repo = str(project.get("repo", ""))
    domain = str(project.get("domain", "SYSTEM"))
    problem = str(project.get("problem", ""))
    stack = list(project.get("stack", []))
    motif = str(project.get("motif", "grid"))

    accent_cycle = [palette.accent, palette.success, palette.warning, palette.accent]
    top_bar_color = accent_cycle[index % len(accent_cycle)]
    delay_s = -(index * 5)

    style_css = f"""
    @keyframes motifBreath {{
      0%, 100% {{ opacity: 1; }}
      50% {{ opacity: 0.52; }}
    }}
    .motif-pulse {{
      animation: motifBreath {loop_s}s ease-in-out infinite;
      animation-delay: {delay_s}s;
    }}
    """

    body_parts: list[str] = []
    # Card shell
    body_parts.append(
        f'  <rect x="1" y="1" width="403" height="196" rx="10" '
        f'fill="{palette.surface}" stroke="{palette.border}" stroke-width="1"/>\n'
        f'  <rect x="1" y="1" width="403" height="3" rx="1.5" fill="{top_bar_color}"/>\n'
    )

    # Domain pill + schematic motif
    domain_pill, _ = render_pill(
        20,
        18,
        domain,
        palette.accent,
        palette.accent_soft,
        palette.border,
        font_size=9.5,
        mono=True,
        pad_x=9,
        height=20,
    )
    body_parts.append(domain_pill)
    body_parts.append(_render_motif(motif, 368, 34, palette))

    # Title + Repo + Arrow
    body_parts.append(
        f'  <text x="20" y="68" class="font-sans" font-size="19" font-weight="700" '
        f'fill="{palette.text_primary}">{escape_xml(name)}</text>\n'
        f'  <text x="20" y="88" class="font-mono" font-size="11" font-weight="600" '
        f'fill="{palette.accent}">{escape_xml(repo)} ↗</text>\n'
    )

    # Problem description (2 lines bounded cleanly)
    lines = wrap_text_lines(problem, max_chars=53, max_lines=2)
    for idx, line in enumerate(lines):
        body_parts.append(
            f'  <text x="20" y="{113 + idx * 17}" class="font-sans" font-size="12" '
            f'fill="{palette.text_muted}">{escape_xml(line)}</text>\n'
        )

    # Divider & bottom stack pills
    body_parts.append(
        f'  <line x1="20" y1="149" x2="385" y2="149" stroke="{palette.border_subtle}" stroke-width="1"/>\n'
    )
    px = 20
    for tech in stack[:4]:
        pill_svg, pw = render_pill(
            px,
            160,
            str(tech),
            palette.text_primary,
            palette.canvas,
            palette.border,
            font_size=10,
            mono=True,
            pad_x=8,
            height=22,
        )
        if px + pw > 386:
            break
        body_parts.append(pill_svg)
        px += pw + 6

    return svg_document(
        width=405,
        height=198,
        title=f"{name} ({repo}) — {domain}",
        desc=f"{problem} Built with {', '.join(str(s) for s in stack)}.",
        style_css=style_css,
        body="".join(body_parts),
    )
