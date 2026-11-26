"""Automated SVG compatibility gate for GitHub <img> sandbox guardrails (2026)."""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

MAX_SVG_BYTES = 350 * 1024  # 350 KB target ceiling
ALLOWED_XML_NS_PREFIXES = (
    "http://www.w3.org/2000/svg",
    "http://www.w3.org/1999/xlink",
    "http://www.w3.org/XML/1998/namespace",
)
URL_PATTERN = re.compile(r"https?://[^\s'\"<>)]+", re.IGNORECASE)
EVENT_ATTR_PATTERN = re.compile(r"^on[a-z]+$", re.IGNORECASE)


def _strip_ns(tag: str) -> str:
    return tag.split("}", 1)[-1] if "}" in tag else tag


def validate_svg_content(content: str, size_bytes: int, label: str = "<memory>") -> list[str]:
    """Return a list of guardrail violations for a single SVG document."""
    violations: list[str] = []

    if size_bytes > MAX_SVG_BYTES:
        violations.append(
            f"{label}: size {size_bytes / 1024:.2f} KB exceeds 350 KB budget"
        )

    try:
        root = ET.fromstring(content)
    except ET.ParseError as exc:
        violations.append(f"{label}: invalid XML ({exc})")
        return violations

    if _strip_ns(root.tag).lower() != "svg":
        violations.append(f"{label}: root element is <{_strip_ns(root.tag)}>, expected <svg>")

    has_title = False
    style_texts: list[str] = []

    for elem in root.iter():
        tag_name = _strip_ns(elem.tag).lower()
        if tag_name == "script":
            violations.append(f"{label}: forbidden <script> element found")
        if tag_name == "foreignobject":
            violations.append(f"{label}: forbidden <foreignObject> element found")
        if tag_name == "title" and (elem.text or "").strip():
            has_title = True
        if tag_name == "style" and elem.text:
            style_texts.append(elem.text)

        for attr_name, attr_val in elem.attrib.items():
            clean_attr = _strip_ns(attr_name)
            if EVENT_ATTR_PATTERN.match(clean_attr):
                violations.append(f"{label}: forbidden JS event attribute '{clean_attr}'")
            if clean_attr.startswith("xmlns"):
                continue
            for match in URL_PATTERN.findall(attr_val):
                if not any(match.startswith(ns) for ns in ALLOWED_XML_NS_PREFIXES):
                    violations.append(f"{label}: forbidden external URL in attribute '{clean_attr}': {match}")

        if elem.text:
            for match in URL_PATTERN.findall(elem.text):
                if not any(match.startswith(ns) for ns in ALLOWED_XML_NS_PREFIXES):
                    violations.append(f"{label}: forbidden external URL in <{tag_name}> text: {match}")

    if not has_title:
        violations.append(f"{label}: missing non-empty <title> element")

    combined_css = "\n".join(style_texts)
    if "@import" in combined_css.lower():
        violations.append(f"{label}: forbidden CSS @import found")
    if "prefers-reduced-motion" not in combined_css:
        violations.append(f"{label}: missing @media (prefers-reduced-motion: reduce) rule")

    return violations


def validate_svg_file(path: Path) -> list[str]:
    """Validate an SVG file on disk."""
    raw = path.read_bytes()
    content = raw.decode("utf-8")
    return validate_svg_content(content, len(raw), label=str(path))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate generated SVGs against GitHub guardrails.")
    parser.add_argument(
        "targets",
        nargs="*",
        type=Path,
        default=[Path("assets/generated")],
        help="SVG files or directories to audit.",
    )
    args = parser.parse_args(argv)

    svg_files: list[Path] = []
    for target in args.targets:
        if target.is_dir():
            svg_files.extend(sorted(target.glob("*.svg")))
        elif target.is_file():
            svg_files.append(target)
        else:
            print(f"[check_svg_compat] ERROR: target not found: {target}", file=sys.stderr)
            return 2

    if not svg_files:
        print("[check_svg_compat] ERROR: no .svg files found to validate.", file=sys.stderr)
        return 2

    all_violations: list[str] = []
    for svg_path in svg_files:
        size_kb = svg_path.stat().st_size / 1024
        file_violations = validate_svg_file(svg_path)
        if file_violations:
            all_violations.extend(file_violations)
            print(f"FAIL  {svg_path} ({size_kb:.2f} KB)")
        else:
            print(f"PASS  {svg_path} ({size_kb:.2f} KB)")

    if all_violations:
        print("\nGuardrail violations detected:", file=sys.stderr)
        for item in all_violations:
            print(f" - {item}", file=sys.stderr)
        return 1

    print(f"\nAll {len(svg_files)} SVG file(s) passed 2026 GitHub sandbox compatibility checks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
