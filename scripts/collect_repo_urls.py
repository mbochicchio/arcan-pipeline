"""
collect_repo_urls.py

This script collects GitHub repository URLs using the GitHub GraphQL API (v4).
It is designed to overcome the 1000-result limitation of GitHub's search API
by segmenting queries into star-count ranges.

Features:
- Filters repositories by programming language (Java, Python, C#),
  star count (>=10), and excludes forks.
- Uses GraphQL pagination to retrieve up to thousands of repositories per language.
- Supports a --test mode that limits the output to just 10 repositories,
  useful for debugging or quick dry runs.
- Stores the collected URLs in a plain text file (`repo_urls.txt`),
  with one URL per line and no duplicates.
- Requires a GitHub personal access token provided in a `.env` file.

Usage:
    python collect_repo_urls.py          # Full run
    python collect_repo_urls.py --test   # Test run (10 repositories max)

Requirements:
    - requests
    - python-dotenv
    - A `.env` file with: GITHUB_TOKEN=your_personal_access_token
"""

import requests
import os
import time
import argparse
from dotenv import load_dotenv

# -------------------------
# Load GitHub token from .env
# -------------------------
load_dotenv()
TOKEN = os.getenv("GITHUB_TOKEN")
if not TOKEN:
    raise RuntimeError("GitHub token not found in .env file")

HEADERS = {"Authorization": f"Bearer {TOKEN}"}
GRAPHQL_URL = "https://api.github.com/graphql"

# -------------------------
# Configuration
# -------------------------
LANGUAGES = ["Java", "Python", "C#"]
STARS_RANGES = [
    "stars:500..1000",
    "stars:200..499",
    "stars:100..199",
    "stars:50..99",
    "stars:25..49",
    "stars:10..24"
]
MAX_REPOS_PER_RANGE = 1000  # GitHub limit per search query
MAX_REPOS_TOTAL = 5000      # Cap per language in full mode
OUTPUT_FILE = "repo_urls.txt"

GRAPHQL_QUERY = """
query ($queryString: String!, $after: String) {
  search(query: $queryString, type: REPOSITORY, first: 100, after: $after) {
    pageInfo {
      hasNextPage
      endCursor
    }
    nodes {
      ... on Repository {
        url
        stargazerCount
        primaryLanguage {
          name
        }
        isFork
      }
    }
  }
}
"""

# -------------------------
# Collect repositories for a language and a stars range
# -------------------------
def collect_repos_for_range(language, stars_range, max_per_range, global_limit):
    print(f"🔎  Querying: language={language}, {stars_range}")
    collected_urls = []
    variables = {
        "queryString": f"language:{language} {stars_range} fork:false",
        "after": None
    }

    while len(collected_urls) < max_per_range and len(collected_urls) < global_limit:
        response = requests.post(
            GRAPHQL_URL,
            json={"query": GRAPHQL_QUERY, "variables": variables},
            headers=HEADERS
        )

        if response.status_code != 200:
            raise Exception(f"GraphQL query failed: {response.text}")

        data = response.json()["data"]["search"]
        for repo in data["nodes"]:
            if not repo["isFork"]:
                collected_urls.append(repo["url"])
                if len(collected_urls) >= global_limit:
                    break

        if not data["pageInfo"]["hasNextPage"]:
            break

        variables["after"] = data["pageInfo"]["endCursor"]
        time.sleep(0.5)

    return collected_urls

# -------------------------
# Main function
# -------------------------
def main(test_mode=False):
    total_limit_per_lang = 10 if test_mode else MAX_REPOS_TOTAL
    all_urls = []

    for lang in LANGUAGES:
        lang_urls = []
        for stars_range in STARS_RANGES:
            if len(lang_urls) >= total_limit_per_lang:
                break
            urls = collect_repos_for_range(
                language=lang,
                stars_range=stars_range,
                max_per_range=MAX_REPOS_PER_RANGE,
                global_limit=total_limit_per_lang - len(lang_urls)
            )
            lang_urls.extend(urls)

        all_urls.extend(lang_urls)
        print(f"✅ Collected {len(lang_urls)} repositories for {lang}")

        if test_mode and len(all_urls) >= 10:
            all_urls = all_urls[:10]
            break

    # Save results
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for url in sorted(set(all_urls)):
            f.write(url + "\n")

    print(f"\n🎉 Finished! {len(all_urls)} repository URLs saved to {OUTPUT_FILE}")

# -------------------------
# Command-line interface
# -------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Collect GitHub repository URLs via GraphQL API with star-range segmentation.")
    parser.add_argument("--test", action="store_true", help="Run in test mode (limit to 10 repositories)")
    args = parser.parse_args()

    main(test_mode=args.test)
