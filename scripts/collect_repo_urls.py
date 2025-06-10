"""
collect_repo_urls.py

This script queries the GitHub GraphQL API to collect up to 100 repositories
per star bucket, written in Python, Java, or C#, with at least 10 stars and
excluding forks. For each matching repository, it saves only the full name
(owner/repo) to a plain text file 'repo_urls.txt'.

The script uses a pagination strategy with defined star ranges (buckets)
to bypass the GitHub GraphQL API’s 1000-item search limit. The '--test'
flag allows running in debug mode, saving only 10 repositories in total.

Environment:
    - A .env file containing a GitHub personal access token:
        GITHUB_TOKEN=your_token_here

Usage:
    python collect_repo_urls.py
    python collect_repo_urls.py --test
"""

import os
import argparse
import requests
from dotenv import load_dotenv

# --- Load GitHub Token from .env file ---
load_dotenv()
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
if not GITHUB_TOKEN:
    raise RuntimeError("GitHub token not found in .env")

HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}"
}

# --- Configuration ---
LANGUAGES = ["Python", "Java", "CSharp"]
MIN_STARS = 10
OUTPUT_FILE = "repo_urls.txt"
MAX_PER_BUCKET = 200  # limit per star bucket (even if GraphQL allows more)
TEST_LIMIT = 10       # number of repos in test mode

# --- Star ranges (buckets) to bypass GitHub GraphQL pagination limits ---
STAR_BUCKETS = [
    (100000, 50000), (49999, 20000), (19999, 10000), (9999, 5000),
    (4999, 2000), (1999, 1000), (999, 500), (499, 100), (99, MIN_STARS)
]

def run_query(query: str) -> dict:
    """
    Executes a GitHub GraphQL query and returns the JSON response.
    """
    response = requests.post(
        "https://api.github.com/graphql",
        json={"query": query},
        headers=HEADERS
    )
    if response.status_code != 200:
        raise RuntimeError(f"GitHub API error: {response.text}")
    return response.json()

def fetch_repositories(language: str, test_mode: bool) -> list[str]:
    """
    Fetches repositories by language and star range, limiting to MAX_PER_BUCKET per range.
    """
    repos = []
    for upper, lower in STAR_BUCKETS:
        cursor = None
        fetched_in_bucket = 0

        while fetched_in_bucket < MAX_PER_BUCKET:
            after = f', after: "{cursor}"' if cursor else ""
            query = f"""
            {{
              search(query: "language:{language} stars:{lower}..{upper} fork:false",
                     type: REPOSITORY, first: 100{after}) {{
                pageInfo {{
                  endCursor
                  hasNextPage
                }}
                edges {{
                  node {{
                    ... on Repository {{
                      nameWithOwner
                    }}
                  }}
                }}
              }}
            }}
            """
            result = run_query(query)
            data = result["data"]["search"]

            for edge in data["edges"]:
                repo_name = edge["node"]["nameWithOwner"]
                if repo_name not in repos:
                    repos.append(repo_name)
                    fetched_in_bucket += 1
                    if test_mode and len(repos) >= TEST_LIMIT:
                        return repos
                    if fetched_in_bucket >= MAX_PER_BUCKET:
                        break

            if not data["pageInfo"]["hasNextPage"]:
                break
            cursor = data["pageInfo"]["endCursor"]

            if test_mode and len(repos) >= TEST_LIMIT:
                return repos
    return repos

def main(test_mode: bool = False):
    """
    Main entry point: iterates over languages and star buckets, collects repository names,
    and writes them to repo_urls.txt.
    """
    all_repos = []
    for lang in LANGUAGES:
        print(f"🔍 Fetching repositories for language: {lang}")
        repos = fetch_repositories(lang, test_mode)
        all_repos.extend(repos)
        if test_mode and len(all_repos) >= TEST_LIMIT:
            break

    # Ensure unique entries
    all_repos = list(dict.fromkeys(all_repos))
    if test_mode:
        all_repos = all_repos[:TEST_LIMIT]

    # Save to output file
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for repo in all_repos:
            f.write(repo + "\n")

    print(f"\n✅ Collected {len(all_repos)} repositories. Saved to '{OUTPUT_FILE}'")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Collect GitHub repository names by language and stars.")
    parser.add_argument("--test", action="store_true", help="Limit to 10 repositories for testing.")
    args = parser.parse_args()
    main(test_mode=args.test)


