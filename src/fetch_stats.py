"""Fetch GitHub contributions and manifest-verified tech stack via GraphQL API."""

from __future__ import annotations

import argparse
import json
import os
import re
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from src.config_loader import load_profile_config

GRAPHQL_ENDPOINT = "https://api.github.com/graphql"

GRAPHQL_QUERY = """
query($login: String!) {
  user(login: $login) {
    repositories(
      first: 12
      orderBy: { field: PUSHED_AT, direction: DESC }
      ownerAffiliations: OWNER
      isFork: false
      privacy: PUBLIC
    ) {
      totalCount
      nodes {
        name
        pushedAt
        primaryLanguage {
          name
        }
        pkgRoot: object(expression: "HEAD:package.json") {
          ... on Blob { text }
        }
        pkgFrontend: object(expression: "HEAD:frontend/package.json") {
          ... on Blob { text }
        }
        pkgWeb: object(expression: "HEAD:web/package.json") {
          ... on Blob { text }
        }
        goRoot: object(expression: "HEAD:go.mod") {
          ... on Blob { text }
        }
        goBackend: object(expression: "HEAD:backend/go.mod") {
          ... on Blob { text }
        }
        pyProject: object(expression: "HEAD:pyproject.toml") {
          ... on Blob { text }
        }
        pyReqs: object(expression: "HEAD:requirements.txt") {
          ... on Blob { text }
        }
        prismaSchema: object(expression: "HEAD:prisma/schema.prisma") {
          ... on Blob { text }
        }
      }
    }
    contributionsCollection {
      totalCommitContributions
      totalPullRequestContributions
      totalIssueContributions
      totalPullRequestReviewContributions
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays {
            contributionCount
          }
        }
      }
    }
  }
}
"""

TECH_RULES: list[tuple[str, str, tuple[str, ...]]] = [
    ("Next.js / React", "Frontend", ('"next"', '"react"')),
    ("TypeScript", "Language", ('"typescript"',)),
    ("Tailwind CSS", "UI", ('"tailwindcss"',)),
    ("Prisma & SQL", "Data", ('"prisma"', '"@prisma/client"', "datasource db")),
    ("Golang (Gin)", "Backend", ("github.com/gin-gonic/gin", "module ")),
    ("Python / AI Stack", "AI", ("torch", "transformers", "timm", "groq", "fastapi", "google-genai")),
]


def _extract_blob_text(node: dict[str, Any], *keys: str) -> str:
    """Concatenate available manifest file texts from a repository node."""
    parts: list[str] = []
    for key in keys:
        blob = node.get(key)
        if isinstance(blob, dict) and isinstance(blob.get("text"), str):
            parts.append(blob["text"].lower())
    return "\n".join(parts)


def extract_manifest_stack(repo_nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Derive active tech stack from dependency manifests of recently pushed repos."""
    counts: dict[str, tuple[str, int]] = {}
    for node in repo_nodes:
        manifest_blob = _extract_blob_text(
            node,
            "pkgRoot",
            "pkgFrontend",
            "pkgWeb",
            "goRoot",
            "goBackend",
            "pyProject",
            "pyReqs",
            "prismaSchema",
        )
        matched_in_repo: set[str] = set()
        for tech_name, category, needles in TECH_RULES:
            if any(needle in manifest_blob for needle in needles):
                matched_in_repo.add(tech_name)
                prev_cat, prev_count = counts.get(tech_name, (category, 0))
                counts[tech_name] = (prev_cat, prev_count + 1)

        # Fallback if a repo has Go/TS/Python primaryLanguage without root manifest
        primary = (node.get("primaryLanguage") or {}).get("name") or ""
        if primary == "TypeScript" and "TypeScript" not in matched_in_repo:
            counts["TypeScript"] = ("Language", counts.get("TypeScript", ("Language", 0))[1] + 1)
        elif primary == "Go" and "Golang (Gin)" not in matched_in_repo:
            counts["Golang (Gin)"] = ("Backend", counts.get("Golang (Gin)", ("Backend", 0))[1] + 1)
        elif primary == "Python" and "Python / AI Stack" not in matched_in_repo:
            counts["Python / AI Stack"] = (
                "AI",
                counts.get("Python / AI Stack", ("AI", 0))[1] + 1,
            )

    if not counts:
        return []

    total_hits = sum(item[1] for item in counts.values())
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1][1], kv[0]))[:5]
    result: list[dict[str, Any]] = []
    running_pct = 0
    for idx, (name, (category, repo_count)) in enumerate(ranked):
        if idx == len(ranked) - 1:
            share_pct = max(1, 100 - running_pct)
        else:
            share_pct = max(1, round((repo_count / total_hits) * 100))
            running_pct += share_pct
        result.append(
            {
                "name": name,
                "category": category,
                "repos_count": repo_count,
                "share_pct": share_pct,
            }
        )
    return result


def derive_engineering_focus(manifest_stack: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Group manifest stack shares into 3 high-level engineering focus buckets."""
    buckets = {
        "Full-Stack Web & UI/UX": 0,
        "Backend & Zero-Trust Data": 0,
        "Applied & Edge AI": 0,
    }
    for item in manifest_stack:
        cat = item.get("category", "")
        pct = int(item.get("share_pct", 0))
        if cat in ("Frontend", "Language", "UI"):
            buckets["Full-Stack Web & UI/UX"] += pct
        elif cat in ("Backend", "Data"):
            buckets["Backend & Zero-Trust Data"] += pct
        else:
            buckets["Applied & Edge AI"] += pct

    total = sum(buckets.values())
    if total <= 0:
        return [
            {"label": "Full-Stack Web & UI/UX", "pct": 42},
            {"label": "Backend & Zero-Trust Data", "pct": 33},
            {"label": "Applied & Edge AI", "pct": 25},
        ]

    normalized: list[dict[str, Any]] = []
    acc = 0
    items = list(buckets.items())
    for idx, (label, val) in enumerate(items):
        if idx == len(items) - 1:
            pct = max(0, 100 - acc)
        else:
            pct = round((val / total) * 100)
            acc += pct
        normalized.append({"label": label, "pct": pct})
    return normalized


def transform_graphql_payload(username: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Normalize GitHub GraphQL response into deterministic cache format (no timestamps)."""
    user = (payload.get("data") or {}).get("user")
    if not user:
        raise ValueError(f"GraphQL response missing user data for {username}")

    contrib = user["contributionsCollection"]
    calendar = contrib["contributionCalendar"]
    weeks = calendar.get("weeks") or []
    recent_weeks = weeks[-12:]
    weekly_activity = [
        sum(int(day.get("contributionCount", 0)) for day in week.get("contributionDays", []))
        for week in recent_weeks
    ]
    while len(weekly_activity) < 12:
        weekly_activity.insert(0, 0)

    repos_conn = user.get("repositories") or {}
    repo_nodes = repos_conn.get("nodes") or []
    manifest_stack = extract_manifest_stack(repo_nodes)
    focus = derive_engineering_focus(manifest_stack)

    return {
        "username": username,
        "data_source": "github_graphql",
        "contributions": {
            "total_contributions": int(calendar.get("totalContributions", 0)),
            "commits": int(contrib.get("totalCommitContributions", 0)),
            "pull_requests": int(contrib.get("totalPullRequestContributions", 0)),
            "issues": int(contrib.get("totalIssueContributions", 0)),
            "reviews": int(contrib.get("totalPullRequestReviewContributions", 0)),
            "public_repos": int(repos_conn.get("totalCount", 0)),
            "weekly_activity": weekly_activity,
        },
        "manifest_stack": manifest_stack,
        "engineering_focus": focus,
    }


def fetch_github_graphql(username: str, token: str) -> dict[str, Any]:
    """Execute GraphQL query against GitHub API using stdlib urllib."""
    if not re.fullmatch(r"[A-Za-z0-9-]+", username):
        raise ValueError(f"Invalid GitHub username: {username}")

    body = json.dumps({"query": GRAPHQL_QUERY, "variables": {"login": username}}).encode("utf-8")
    req = urllib.request.Request(
        GRAPHQL_ENDPOINT,
        data=body,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": f"{username}-profile-generator/2026",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        payload = json.loads(resp.read().decode("utf-8"))

    if payload.get("errors"):
        raise RuntimeError(f"GitHub GraphQL returned errors: {payload['errors']}")

    return transform_graphql_payload(username, payload)


def load_or_update_stats(
    config_path: Path,
    cache_path: Path,
    offline: bool = False,
) -> dict[str, Any]:
    """Load cached stats in offline mode or refresh deterministically from GitHub GraphQL."""
    config = load_profile_config(config_path)
    username = config["profile"]["username"]

    cached: dict[str, Any] = {}
    if cache_path.exists():
        cached = json.loads(cache_path.read_text(encoding="utf-8"))

    if offline:
        if not cached:
            raise FileNotFoundError(f"Offline mode requested but cache not found: {cache_path}")
        return cached

    token = os.environ.get("PROFILE_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not token:
        if cached:
            return cached
        raise RuntimeError("No PROFILE_TOKEN/GITHUB_TOKEN set and no stats_cache.json available.")

    try:
        fresh = fetch_github_graphql(username, token)
        # Preserve cached manifest_stack if remote repos have no readable manifests
        if not fresh["manifest_stack"] and cached.get("manifest_stack"):
            fresh["manifest_stack"] = cached["manifest_stack"]
            fresh["engineering_focus"] = derive_engineering_focus(fresh["manifest_stack"])

        serialized = json.dumps(fresh, indent=2) + "\n"
        existing = cache_path.read_text(encoding="utf-8") if cache_path.exists() else ""
        if serialized != existing:
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            cache_path.write_text(serialized, encoding="utf-8")
        return fresh
    except (urllib.error.URLError, RuntimeError, ValueError) as exc:
        if cached:
            print(f"[fetch_stats] Warning: falling back to cache ({exc})")
            return cached
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch GitHub stats and manifest stack.")
    parser.add_argument("--config", type=Path, default=Path("profile.config.toml"))
    parser.add_argument("--cache", type=Path, default=Path("data/stats_cache.json"))
    parser.add_argument("--offline", action="store_true", help="Use local cache without API calls.")
    args = parser.parse_args()

    stats = load_or_update_stats(args.config, args.cache, offline=args.offline)
    print(
        f"[fetch_stats] Ready for @{stats['username']} "
        f"(source={stats['data_source']}, total={stats['contributions']['total_contributions']})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
