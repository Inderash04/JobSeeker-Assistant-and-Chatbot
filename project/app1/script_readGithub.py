"""
github_analyzer.py

Fetches a GitHub user's public repo data and turns it into a compact,
LLM-friendly summary. This is the "real data" input for the gap analysis —
the whole point of this step is to replace guesswork with facts.
"""

import os
import requests
from datetime import datetime, timezone
from dotenv import load_dotenv
load_dotenv()


GITHUB_API = "https://api.github.com"

# Personal access token — create one at github.com/settings/tokens
# (needs no special scopes for public data, just raises your rate limit)
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")

HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}" if GITHUB_TOKEN else "",
    "Accept": "application/vnd.github+json",
}


def get_user_repos(username: str) -> list[dict]:
    """Fetch all public, non-fork repos for a user, sorted by last updated."""
    repos = []
    page = 1
    while True:
        resp = requests.get(
            f"{GITHUB_API}/users/{username}/repos",
            headers=HEADERS,
            params={"per_page": 100, "page": page, "sort": "updated"},
        )
        resp.raise_for_status()
        batch = resp.json()
        if not batch:
            break
        repos.extend(batch)
        page += 1
        if page > 5:  # safety cap — 500 repos is plenty for this use case
            break

    # Filter out forks — we care about original work, not cloned repos
    return [r for r in repos if not r.get("fork")]


def get_repo_languages(owner: str, repo: str) -> dict:
    """Returns {language: bytes_of_code} for a single repo."""
    resp = requests.get(
        f"{GITHUB_API}/repos/{owner}/{repo}/languages", headers=HEADERS
    )
    resp.raise_for_status()
    return resp.json()


def months_since(date_str: str) -> float:
    dt = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    delta = datetime.now(timezone.utc) - dt
    return round(delta.days / 30, 1)


def summarize_profile(username: str, max_repos: int = 15) -> dict:
    """
    Builds a compact summary of a user's GitHub activity — this is the
    object we hand to the LLM for gap analysis. Keeping it compact matters:
    an LLM reasons better over a clean summary than raw API JSON.
    """
    repos = get_user_repos(username)[:max_repos]

    language_totals: dict[str, int] = {}
    repo_summaries = []

    for r in repos:
        owner = r["owner"]["login"]
        name = r["name"]
        try:
            langs = get_repo_languages(owner, name)
        except requests.HTTPError:
            langs = {}

        for lang, byte_count in langs.items():
            language_totals[lang] = language_totals.get(lang, 0) + byte_count

        repo_summaries.append({
            "name": name,
            "description": r.get("description") or "",
            "languages": list(langs.keys()),
            "stars": r.get("stargazers_count", 0),
            "months_since_last_update": months_since(r["updated_at"]),
            "has_readme_description": bool(r.get("description")),
        })

    # Rank languages by total bytes written — proxy for depth, not just exposure
    ranked_languages = sorted(
        language_totals.items(), key=lambda x: x[1], reverse=True
    )
    top_languages = [lang for lang, _ in ranked_languages[:8]]

    return {
        "username": username,
        "total_public_repos_analyzed": len(repos),
        "top_languages_by_code_volume": top_languages,
        "repos": repo_summaries,
    }

if __name__ == "__main__":
    import json
    import sys
 
    username = sys.argv[1] if len(sys.argv) > 1 else "torvalds"
    profile = summarize_profile(username)
    print(json.dumps(profile, indent=2))
 
