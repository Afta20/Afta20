"""Bento Telemetry Dashboard SVG generator (3-panel Editorial Bento)."""

from __future__ import annotations

from typing import Any

from src.config_loader import escape_xml
from src.svg.primitives import render_bento_panel, render_pill, svg_document
from src.svg.theme import get_palette


def render_bento_svg(config: dict[str, Any], stats: dict[str, Any], mode: str) -> str:
    """Render 960x346 3-panel Bento Telemetry Dashboard for Dark or Light mode."""
    theme_cfg = config.get("theme", {})
    loop_s = int(theme_cfg.get("loop_seconds", 24))
    palette = get_palette(mode, theme_cfg)

    contrib = stats.get("contributions", {})
    total_contrib = int(contrib.get("total_contributions", 0))
    commits = int(contrib.get("commits", 0))
    prs = int(contrib.get("pull_requests", 0))
    reviews = int(contrib.get("reviews", 0))
    public_repos = int(contrib.get("public_repos", 0))
    weekly = [int(v) for v in (contrib.get("weekly_activity") or [0] * 12)][:12]
    while len(weekly) < 12:
        weekly.insert(0, 0)

    data_source = str(stats.get("data_source", "offline_snapshot"))
    is_live = data_source == "github_graphql"
    source_label = "LIVE GRAPHQL" if is_live else "SNAPSHOT"
    source_fg = palette.success if is_live else palette.accent
    source_bg = palette.success_soft if is_live else palette.accent_soft

    manifest_stack = list(stats.get("manifest_stack") or [])[:5]
    focus_items = list(stats.get("engineering_focus") or [])[:3]

    style_css = f"""
    @keyframes barBreathe {{
      0%, 100% {{ opacity: 1; }}
      50% {{ opacity: 0.72; }}
    }}
    @keyframes sparkWave {{
      0%, 100% {{ opacity: 0.92; }}
      50% {{ opacity: 0.55; }}
    }}
    .stack-bar-0 {{ animation: barBreathe {loop_s}s ease-in-out infinite; animation-delay: 0s; }}
    .stack-bar-1 {{ animation: barBreathe {loop_s}s ease-in-out infinite; animation-delay: -4s; }}
    .stack-bar-2 {{ animation: barBreathe {loop_s}s ease-in-out infinite; animation-delay: -8s; }}
    .stack-bar-3 {{ animation: barBreathe {loop_s}s ease-in-out infinite; animation-delay: -12s; }}
    .stack-bar-4 {{ animation: barBreathe {loop_s}s ease-in-out infinite; animation-delay: -16s; }}
    .spark-bar {{ animation: sparkWave {loop_s}s ease-in-out infinite; }}
    """ + "\n".join(
        f"    .spark-{i} {{ animation-delay: -{i * 2}s; }}" for i in range(12)
    ) + """
    """

    body_parts: list[str] = []
    body_parts.append(
        f'  <rect x="1" y="1" width="958" height="344" rx="12" '
        f'fill="{palette.canvas}" stroke="{palette.border}" stroke-width="1"/>\n'
    )

    # =========================================================================
    # Panel 1 (Left, x=16..314): Contribution Telemetry
    # =========================================================================
    body_parts.append(render_bento_panel(16, 16, 298, 314, palette, radius=10))
    body_parts.append(
        f'  <text x="34" y="42" class="font-mono" font-size="10.5" font-weight="700" '
        f'letter-spacing="0.8" fill="{palette.text_muted}">TELEMETRY</text>\n'
    )
    _, pill_w = render_pill(0, 26, source_label, source_fg, source_bg, palette.border, 9.5, True, 8, 20)
    source_pill, _ = render_pill(
        298 - pill_w, 26, source_label, source_fg, source_bg, palette.border, 9.5, True, 8, 20
    )
    body_parts.append(source_pill)

    body_parts.append(
        f'  <text x="34" y="84" class="font-sans" font-size="32" font-weight="700" '
        f'fill="{palette.text_primary}">{total_contrib:,}</text>\n'
        f'  <text x="{34 + len(f"{total_contrib:,}") * 19 + 10}" y="82" class="font-sans" '
        f'font-size="12" fill="{palette.text_muted}">contributions / yr</text>\n'
    )

    # 2x2 sub-cards
    tiles = [
        (32, 102, "Commits", f"{commits:,}", palette.accent),
        (170, 102, "Pull Requests", f"{prs:,}", palette.success),
        (32, 156, "Reviews", f"{reviews:,}", palette.warning),
        (170, 156, "Public Repos", f"{public_repos:,}", palette.text_primary),
    ]
    for tx, ty, tlabel, tval, tcolor in tiles:
        body_parts.append(
            f'  <rect x="{tx}" y="{ty}" width="128" height="46" rx="8" '
            f'fill="{palette.canvas}" stroke="{palette.border_subtle}" stroke-width="1"/>\n'
            f'  <text x="{tx + 12}" y="{ty + 18}" class="font-sans" font-size="10.5" '
            f'fill="{palette.text_muted}">{escape_xml(tlabel)}</text>\n'
            f'  <text x="{tx + 12}" y="{ty + 37}" class="font-mono" font-size="15" font-weight="700" '
            f'fill="{tcolor}">{escape_xml(tval)}</text>\n'
        )

    # 12-week cadence sparkline
    body_parts.append(
        f'  <text x="34" y="228" class="font-mono" font-size="10" font-weight="700" '
        f'letter-spacing="0.6" fill="{palette.text_muted}">12-WEEK ACTIVITY CADENCE</text>\n'
        f'  <line x1="34" y1="304" x2="296" y2="304" stroke="{palette.border_subtle}" stroke-width="1"/>\n'
    )
    max_week = max(max(weekly), 1)
    for idx, val in enumerate(weekly):
        bar_h = max(6, round((val / max_week) * 58))
        bx = 34 + idx * 22
        by = 304 - bar_h
        bar_fill = palette.accent if idx >= 8 else palette.success if idx >= 4 else palette.border
        body_parts.append(
            f'  <rect x="{bx}" y="{by}" width="16" height="{bar_h}" rx="3" '
            f'fill="{bar_fill}" class="spark-bar spark-{idx}"/>\n'
        )
    body_parts.append(
        f'  <text x="34" y="318" class="font-mono" font-size="9.5" fill="{palette.text_muted}">-12w</text>\n'
        f'  <text x="296" y="318" text-anchor="end" class="font-mono" font-size="9.5" fill="{palette.text_muted}">Now</text>\n'
    )

    # =========================================================================
    # Panel 2 (Center, x=328..692): Manifest-Verified Tech Stack
    # =========================================================================
    body_parts.append(render_bento_panel(328, 16, 364, 314, palette, radius=10))
    body_parts.append(
        f'  <text x="348" y="42" class="font-mono" font-size="10.5" font-weight="700" '
        f'letter-spacing="0.8" fill="{palette.text_muted}">MANIFEST-VERIFIED STACK</text>\n'
        f'  <text x="348" y="60" class="font-sans" font-size="11.5" '
        f'fill="{palette.text_muted}">Derived from active repo manifests (not byte counts)</text>\n'
        f'  <line x1="348" y1="74" x2="672" y2="74" stroke="{palette.border_subtle}" stroke-width="1"/>\n'
    )

    stack_colors = [
        palette.accent,
        palette.success,
        palette.warning,
        palette.accent,
        palette.danger,
    ]
    for idx, item in enumerate(manifest_stack):
        row_y = 100 + idx * 46
        name = str(item.get("name", ""))
        repos_cnt = int(item.get("repos_count", 0))
        share = int(item.get("share_pct", 0))
        bar_w = max(14, round((min(100, max(0, share)) / 100) * 324))
        bar_color = stack_colors[idx % len(stack_colors)]
        meta_txt = f"{repos_cnt} repo{'s' if repos_cnt != 1 else ''} · {share}%"

        body_parts.append(
            f'  <text x="348" y="{row_y}" class="font-sans" font-size="12.5" font-weight="600" '
            f'fill="{palette.text_primary}">{escape_xml(name[:34])}</text>\n'
            f'  <text x="672" y="{row_y}" text-anchor="end" class="font-mono" font-size="11" '
            f'fill="{palette.text_muted}">{escape_xml(meta_txt)}</text>\n'
            f'  <rect x="348" y="{row_y + 10}" width="324" height="8" rx="4" fill="{palette.bar_track}"/>\n'
            f'  <rect x="348" y="{row_y + 10}" width="{bar_w}" height="8" rx="4" '
            f'fill="{bar_color}" class="stack-bar-{idx}"/>\n'
        )

    # =========================================================================
    # Panel 3 (Right, x=706..944): Engineering Focus & System Signals
    # =========================================================================
    body_parts.append(render_bento_panel(706, 16, 238, 314, palette, radius=10))
    body_parts.append(
        f'  <text x="724" y="42" class="font-mono" font-size="10.5" font-weight="700" '
        f'letter-spacing="0.8" fill="{palette.text_muted}">ENGINEERING FOCUS</text>\n'
    )
    focus_colors = [palette.accent, palette.success, palette.warning]
    for idx, focus in enumerate(focus_items):
        fy = 74 + idx * 46
        flabel = str(focus.get("label", ""))
        fpct = int(focus.get("pct", 0))
        fw = max(12, round((min(100, max(0, fpct)) / 100) * 202))
        fcol = focus_colors[idx % len(focus_colors)]
        body_parts.append(
            f'  <text x="724" y="{fy}" class="font-sans" font-size="11.5" font-weight="600" '
            f'fill="{palette.text_primary}">{escape_xml(flabel[:26])}</text>\n'
            f'  <text x="926" y="{fy}" text-anchor="end" class="font-mono" font-size="11" '
            f'font-weight="700" fill="{fcol}">{fpct}%</text>\n'
            f'  <rect x="724" y="{fy + 9}" width="202" height="7" rx="3.5" fill="{palette.bar_track}"/>\n'
            f'  <rect x="724" y="{fy + 9}" width="{fw}" height="7" rx="3.5" fill="{fcol}"/>\n'
        )

    body_parts.append(
        f'  <line x1="724" y1="210" x2="926" y2="210" stroke="{palette.border_subtle}" stroke-width="1"/>\n'
        f'  <text x="724" y="234" class="font-mono" font-size="10" font-weight="700" '
        f'letter-spacing="0.7" fill="{palette.text_muted}">SHIPPED HIGHLIGHTS</text>\n'
    )
    signals = [
        ("Maritime UI", "React-Leaflet · Live"),
        ("Healthcare", "Zero-Trust · Go Gin"),
        ("Edge Vision", "MobileViT · Gemma 4"),
    ]
    for idx, (k, v) in enumerate(signals):
        sy = 260 + idx * 25
        body_parts.append(
            f'  <text x="724" y="{sy}" class="font-sans" font-size="11" '
            f'fill="{palette.text_muted}">{escape_xml(k)}</text>\n'
            f'  <text x="926" y="{sy}" text-anchor="end" class="font-mono" font-size="11" '
            f'font-weight="600" fill="{palette.text_primary}">{escape_xml(v)}</text>\n'
        )

    username = str(config["profile"].get("username", "Afta20"))
    title = f"@{username} Telemetry & Manifest-Verified Stack"
    desc = (
        f"{total_contrib} yearly contributions ({commits} commits, {prs} PRs, {reviews} reviews) "
        f"and manifest-verified tech stack."
    )
    return svg_document(
        width=960,
        height=346,
        title=title,
        desc=desc,
        style_css=style_css,
        body="".join(body_parts),
    )
