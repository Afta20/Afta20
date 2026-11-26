"""Unit tests for Afta20 GitHub Profile README generator and compatibility gate."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.check_svg_compat import MAX_SVG_BYTES, validate_svg_content
from src.config_loader import escape_xml, load_profile_config
from src.fetch_stats import extract_manifest_stack, transform_graphql_payload
from src.render_svg import build_all_svgs

REPO_ROOT = Path(__file__).resolve().parent.parent


class GeneratorTestSuite(unittest.TestCase):
    def test_load_profile_config_toml(self) -> None:
        cfg = load_profile_config(REPO_ROOT / "profile.config.toml")
        self.assertEqual(cfg["profile"]["username"], "Afta20")
        self.assertEqual(len(cfg["projects"]), 4)

    def test_escape_xml(self) -> None:
        raw = '<Afta & "20">'
        self.assertEqual(escape_xml(raw), "&lt;Afta &amp; &quot;20&quot;&gt;")

    def test_extract_manifest_stack_and_determinism(self) -> None:
        payload = {
            "data": {
                "user": {
                    "repositories": {
                        "totalCount": 4,
                        "nodes": [
                            {
                                "name": "AksaMedika",
                                "primaryLanguage": {"name": "TypeScript"},
                                "pkgFrontend": {"text": '{"dependencies":{"next":"15.0.0","typescript":"5.0.0"}}'},
                                "goBackend": {"text": "module aksamedika\nrequire github.com/gin-gonic/gin v1.10.0"},
                            },
                            {
                                "name": "Poseidon_Fleet",
                                "primaryLanguage": {"name": "TypeScript"},
                                "pkgRoot": {"text": '{"dependencies":{"next":"15.0.0","tailwindcss":"4.0.0"}}'},
                                "prismaSchema": {"text": "datasource db { provider = \"postgresql\" }"},
                            },
                        ],
                    },
                    "contributionsCollection": {
                        "totalCommitContributions": 120,
                        "totalPullRequestContributions": 15,
                        "totalIssueContributions": 5,
                        "totalPullRequestReviewContributions": 8,
                        "contributionCalendar": {
                            "totalContributions": 148,
                            "weeks": [
                                {"contributionDays": [{"contributionCount": 2}, {"contributionCount": 3}]}
                            ],
                        },
                    },
                }
            }
        }
        a = transform_graphql_payload("Afta20", payload)
        b = transform_graphql_payload("Afta20", payload)
        self.assertEqual(a, b)
        self.assertEqual(len(a["contributions"]["weekly_activity"]), 12)
        names = [item["name"] for item in a["manifest_stack"]]
        self.assertIn("Next.js / React", names)
        self.assertIn("Golang (Gin)", names)

        # Ensure extract_manifest_stack handles empty nodes safely
        self.assertEqual(extract_manifest_stack([]), [])

    def test_offline_build_deterministic_and_compat_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tmp1, tempfile.TemporaryDirectory() as tmp2:
            files1 = build_all_svgs(
                REPO_ROOT / "profile.config.toml",
                REPO_ROOT / "data/stats_cache.json",
                Path(tmp1),
                offline=True,
            )
            files2 = build_all_svgs(
                REPO_ROOT / "profile.config.toml",
                REPO_ROOT / "data/stats_cache.json",
                Path(tmp2),
                offline=True,
            )
            self.assertEqual(len(files1), 12)
            for p1, p2 in zip(files1, files2):
                content1 = p1.read_text(encoding="utf-8")
                content2 = p2.read_text(encoding="utf-8")
                self.assertEqual(content1, content2, f"Non-deterministic output in {p1.name}")
                violations = validate_svg_content(content1, p1.stat().st_size, label=p1.name)
                self.assertEqual(violations, [], f"Violations in {p1.name}: {violations}")

    def test_compat_checker_rejects_forbidden_patterns(self) -> None:
        base_ok = (
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
            "<title>Test</title>"
            "<defs><style>@media (prefers-reduced-motion: reduce) { * { animation: none !important; } }</style></defs>"
            '<rect width="10" height="10"/>'
            "</svg>"
        )
        self.assertEqual(validate_svg_content(base_ok, len(base_ok)), [])

        with_script = base_ok.replace("<rect", "<script>alert(1)</script><rect")
        self.assertTrue(any("<script>" in v for v in validate_svg_content(with_script, len(with_script))))

        with_foreign = base_ok.replace("<rect", "<foreignObject><div>x</div></foreignObject><rect")
        self.assertTrue(
            any("<foreignObject>" in v for v in validate_svg_content(with_foreign, len(with_foreign)))
        )

        with_ext_url = base_ok.replace('height="10"', 'height="10" data-src="https://evil.example/a.png"')
        self.assertTrue(
            any("external URL" in v for v in validate_svg_content(with_ext_url, len(with_ext_url)))
        )

        no_motion = base_ok.replace("prefers-reduced-motion", "prefers-color-scheme")
        self.assertTrue(
            any("prefers-reduced-motion" in v for v in validate_svg_content(no_motion, len(no_motion)))
        )

        no_title = base_ok.replace("<title>Test</title>", "")
        self.assertTrue(any("<title>" in v for v in validate_svg_content(no_title, len(no_title))))

        oversized = validate_svg_content(base_ok, MAX_SVG_BYTES + 1024)
        self.assertTrue(any("exceeds 350 KB" in v for v in oversized))


if __name__ == "__main__":
    unittest.main()
