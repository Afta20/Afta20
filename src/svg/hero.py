"""Hero Command Banner SVG generator (Editorial Bento style)."""

from __future__ import annotations

from typing import Any

from src.config_loader import escape_xml
from src.svg.primitives import (
    render_bento_panel,
    render_pill,
    svg_document,
    wrap_text_lines,
)
from src.svg.theme import get_palette


def render_hero_svg(config: dict[str, Any], stats: dict[str, Any], mode: str) -> str:
    """Render 960x276 Editorial Bento Hero Command Banner for Dark or Light mode."""
    profile = config["profile"]
    theme_cfg = config.get("theme", {})
    pillars = list(config.get("pillars", {}).get("items", []))[:3]
    loop_s = int(theme_cfg.get("loop_seconds", 24))
    palette = get_palette(mode, theme_cfg)

    display_name = str(profile.get("display_name", "Afreeza Prananta"))
    handle = str(profile.get("handle", "@Afta20"))
    headline = str(profile.get("headline", "Full-Stack Engineer & UI/UX Designer"))
    tagline = str(profile.get("tagline", ""))
    availability = str(profile.get("availability", "Open to Roles"))
    location = str(profile.get("location", "Indonesia · UTC+7"))
    project_count = len(config.get("projects", []))

    style_css = f"""
    @keyframes beaconPulse {{
      0%, 100% {{ transform: scale(1); opacity: 0.35; }}
      50% {{ transform: scale(1.75); opacity: 0.08; }}
    }}
    @keyframes traceFlow {{
      0% {{ stroke-dashoffset: 0; }}
      100% {{ stroke-dashoffset: -120; }}
    }}
    @keyframes pillarBreath {{
      0%, 100% {{ opacity: 1; }}
      50% {{ opacity: 0.62; }}
    }}
    .beacon-ring {{
      transform-box: fill-box;
      transform-origin: center;
      animation: beaconPulse {loop_s}s ease-in-out infinite;
      animation-delay: -6s;
    }}
    .trace-flow {{
      stroke-dasharray: 18 12;
      animation: traceFlow {loop_s}s linear infinite;
      animation-delay: -9s;
    }}
    .pillar-0 {{ animation: pillarBreath {loop_s}s ease-in-out infinite; animation-delay: 0s; }}
    .pillar-1 {{ animation: pillarBreath {loop_s}s ease-in-out infinite; animation-delay: -{loop_s // 3}s; }}
    .pillar-2 {{ animation: pillarBreath {loop_s}s ease-in-out infinite; animation-delay: -{(2 * loop_s) // 3}s; }}
    """

    defs_extra = (
        f'    <pattern id="hero-grid-{mode}" width="18" height="18" patternUnits="userSpaceOnUse">\n'
        f'      <circle cx="2" cy="2" r="0.9" fill="{palette.grid_dot}" opacity="0.65"/>\n'
        f'    </pattern>\n'
        f'    <linearGradient id="hero-accent-grad-{mode}" x1="0%" y1="0%" x2="100%" y2="0%">\n'
        f'      <stop offset="0%" stop-color="{palette.accent}"/>\n'
        f'      <stop offset="100%" stop-color="{palette.success}"/>\n'
        f'    </linearGradient>\n'
    )

    body_parts: list[str] = []
    # Outer GitHub-harmonized canvas
    body_parts.append(
        f'  <rect x="1" y="1" width="958" height="274" rx="12" '
        f'fill="{palette.canvas}" stroke="{palette.border}" stroke-width="1"/>\n'
    )

    # Left main identity panel (604x244)
    body_parts.append(render_bento_panel(16, 16, 604, 244, palette, radius=10))
    body_parts.append(
        f'  <rect x="17" y="17" width="602" height="242" rx="9" '
        f'fill="url(#hero-grid-{mode})" opacity="0.55"/>\n'
    )
    # Top accent hairline inside left card
    body_parts.append(
        f'  <rect x="16" y="16" width="604" height="3" rx="1.5" '
        f'fill="url(#hero-accent-grad-{mode})"/>\n'
    )

    # Status beacon + eyebrow
    body_parts.append(
        f'  <circle cx="42" cy="44" r="8" fill="{palette.success}" class="beacon-ring"/>\n'
        f'  <circle cx="42" cy="44" r="4.2" fill="{palette.success}"/>\n'
        f'  <text x="58" y="48" class="font-mono" font-size="11.5" font-weight="700" '
        f'letter-spacing="0.8" fill="{palette.accent}">AFTA20 // COMMAND CENTER</text>\n'
    )

    # Availability pill right-aligned inside left card (right edge = 602)
    avail_pill_tmp, avail_w = render_pill(
        0,
        33,
        availability,
        palette.success,
        palette.success_soft,
        palette.border,
        font_size=10.5,
        mono=False,
        pad_x=10,
        height=22,
    )
    avail_x = max(320, 602 - avail_w)
    avail_pill, _ = render_pill(
        avail_x,
        33,
        availability,
        palette.success,
        palette.success_soft,
        palette.border,
        font_size=10.5,
        mono=False,
        pad_x=10,
        height=22,
    )
    body_parts.append(avail_pill)

    # Identity display name + handle
    body_parts.append(
        f'  <text x="36" y="100" class="font-sans" font-size="31" font-weight="700" '
        f'letter-spacing="-0.6" fill="{palette.text_primary}">{escape_xml(display_name)}</text>\n'
    )
    handle_x = 36 + round(len(display_name) * 16.4) + 12
    handle_pill, _ = render_pill(
        min(handle_x, 510),
        79,
        handle,
        palette.text_muted,
        palette.surface_alt,
        palette.border,
        font_size=11,
        mono=True,
        pad_x=9,
        height=22,
    )
    body_parts.append(handle_pill)

    # Headline
    body_parts.append(
        f'  <text x="36" y="130" class="font-sans" font-size="16" font-weight="600" '
        f'fill="{palette.accent}">{escape_xml(headline)}</text>\n'
    )

    # Tagline (2 lines bounded cleanly)
    tagline_lines = wrap_text_lines(tagline, max_chars=70, max_lines=2)
    for idx, line in enumerate(tagline_lines):
        body_parts.append(
            f'  <text x="36" y="{160 + idx * 21}" class="font-sans" font-size="13.5" '
            f'fill="{palette.text_muted}">{escape_xml(line)}</text>\n'
        )

    # Bottom divider & compact metadata chips
    body_parts.append(
        f'  <line x1="36" y1="208" x2="600" y2="208" stroke="{palette.border_subtle}" stroke-width="1"/>\n'
    )
    meta_items = [
        f"{project_count} Flagship Systems",
        "Next.js 15 · Go · Edge AI",
        location,
    ]
    chip_x = 36
    for item in meta_items:
        chip_svg, chip_w = render_pill(
            chip_x,
            220,
            item,
            palette.text_primary,
            palette.canvas,
            palette.border,
            font_size=10.5,
            mono=True,
            pad_x=9,
            height=22,
        )
        body_parts.append(chip_svg)
        chip_x += chip_w + 8

    # Right Top Card: Architectural Telemetry Trace (310x106)
    body_parts.append(render_bento_panel(634, 16, 310, 106, palette, radius=10))
    body_parts.append(
        f'  <text x="652" y="40" class="font-mono" font-size="10.5" font-weight="700" '
        f'letter-spacing="0.8" fill="{palette.text_muted}">ARCHITECTURE TELEMETRY</text>\n'
        f'  <path d="M 652 62 L 728 62 L 744 50 L 836 50 L 852 62 L 926 62" '
        f'fill="none" stroke="{palette.border}" stroke-width="1.5"/>\n'
        f'  <path d="M 652 62 L 728 62 L 744 50 L 836 50 L 852 62 L 926 62" '
        f'fill="none" stroke="{palette.accent}" stroke-width="2" class="trace-flow"/>\n'
        f'  <circle cx="652" cy="62" r="3" fill="{palette.accent}"/>\n'
        f'  <circle cx="790" cy="50" r="3" fill="{palette.success}"/>\n'
        f'  <circle cx="926" cy="62" r="3" fill="{palette.accent}"/>\n'
        f'  <text x="652" y="88" class="font-sans" font-size="12.5" font-weight="600" '
        f'fill="{palette.text_primary}">Full-Stack · Zero-Trust · Edge AI</text>\n'
        f'  <text x="652" y="106" class="font-mono" font-size="10.5" '
        f'fill="{palette.text_muted}">Self-contained Primer SVG · Zero 503</text>\n'
    )

    # Right Bottom Card: Core Engineering Pillars (310x126)
    body_parts.append(render_bento_panel(634, 134, 310, 126, palette, radius=10))
    body_parts.append(
        f'  <text x="652" y="158" class="font-mono" font-size="10.5" font-weight="700" '
        f'letter-spacing="0.8" fill="{palette.text_muted}">CORE DOMAINS</text>\n'
    )
    dot_colors = [palette.accent, palette.success, palette.warning]
    for idx, pillar in enumerate(pillars):
        row_y = 184 + idx * 28
        dot_color = dot_colors[idx % len(dot_colors)]
        body_parts.append(
            f'  <g class="pillar-{idx}">\n'
            f'    <rect x="652" y="{row_y - 12}" width="22" height="17" rx="4" '
            f'fill="{palette.surface_alt}" stroke="{palette.border}" stroke-width="1"/>\n'
            f'    <text x="663" y="{row_y}" text-anchor="middle" class="font-mono" '
            f'font-size="10" font-weight="700" fill="{dot_color}">0{idx + 1}</text>\n'
            f'    <text x="683" y="{row_y}" class="font-sans" font-size="12.5" font-weight="600" '
            f'fill="{palette.text_primary}">{escape_xml(pillar[:34])}</text>\n'
            f'  </g>\n'
        )

    title = f"{display_name} ({handle}) — {headline}"
    desc = f"{tagline} Core pillars: {', '.join(pillars)}."
    return svg_document(
        width=960,
        height=276,
        title=title,
        desc=desc,
        style_css=style_css,
        body="".join(body_parts),
        defs_extra=defs_extra,
    )
