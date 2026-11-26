"""Main SVG build orchestrator for Afta20 GitHub Profile README."""

from __future__ import annotations

import argparse
from pathlib import Path

from src.config_loader import load_profile_config
from src.fetch_stats import load_or_update_stats
from src.svg.bento import render_bento_svg
from src.svg.hero import render_hero_svg
from src.svg.project_card import render_project_card_svg


def build_all_svgs(
    config_path: Path,
    cache_path: Path,
    out_dir: Path,
    offline: bool = False,
) -> list[Path]:
    """Generate deterministic Dark and Light SVG pairs into out_dir."""
    config = load_profile_config(config_path)
    stats = load_or_update_stats(config_path, cache_path, offline=offline)
    theme_cfg = config.get("theme", {})
    projects = list(config.get("projects", []))

    out_dir.mkdir(parents=True, exist_ok=True)
    generated: list[Path] = []

    for mode in ("dark", "light"):
        hero_path = out_dir / f"hero-{mode}.svg"
        hero_path.write_text(render_hero_svg(config, stats, mode), encoding="utf-8")
        generated.append(hero_path)

        bento_path = out_dir / f"bento-{mode}.svg"
        bento_path.write_text(render_bento_svg(config, stats, mode), encoding="utf-8")
        generated.append(bento_path)

        for idx, project in enumerate(projects):
            slug = str(project["slug"])
            card_path = out_dir / f"project-{slug}-{mode}.svg"
            card_path.write_text(
                render_project_card_svg(project, theme_cfg, mode, index=idx),
                encoding="utf-8",
            )
            generated.append(card_path)

    return generated


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Editorial Bento SVG assets.")
    parser.add_argument("--config", type=Path, default=Path("profile.config.toml"))
    parser.add_argument("--cache", type=Path, default=Path("data/stats_cache.json"))
    parser.add_argument("--out-dir", type=Path, default=Path("assets/generated"))
    parser.add_argument("--offline", action="store_true", help="Build from local cache only.")
    args = parser.parse_args()

    files = build_all_svgs(args.config, args.cache, args.out_dir, offline=args.offline)
    for path in files:
        size_kb = path.stat().st_size / 1024
        print(f"[render_svg] {path} ({size_kb:.2f} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
