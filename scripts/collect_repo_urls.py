"""
collect_repo_urls.py

This script queries the GitHub GraphQL API to retrieve repositories written in Python, Java, or C#,
filtered by a minimum of 10 stars and excluding forks. It saves the full repository name (owner/repo),
URL, stargazer count, and programming language to a CSV file named 'repository_list_urls.csv'.

The script supports a '--test' flag that limits the output to 10 repositories total for debugging purposes.
It uses GraphQL pagination with star buckets to overcome GitHub's 1000-result limitation per query.

Requirements:
    - python-dotenv
    - requests

Environment:
    - Requires a .env file with a GITHUB_TOKEN entry.

Usage:
    python collect_repo_urls.py
    python collect_repo_urls.py --test
"""

import os
import csv
import argparse
import requests # type: ignore
from dotenv import load_dotenv # type: ignore

load_dotenv()
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

if not GITHUB_TOKEN:
    raise RuntimeError("GitHub token not found in .env")

HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}"
}

LANGUAGES = ["Python", "Java", "CSharp"]
MIN_STARS = 10
OUTPUT_CSV = "repository_list_urls.csv"

# Define star buckets to paginate around the 1000 result GraphQL limitation
STAR_BUCKETS = [
    (100000, 50000), (49999, 20000), (19999, 10000), (9999, 5000),
    (4999, 2000), (1999, 1000), (999, 500), (499, 100), (99, MIN_STARS)
]

def run_query(query):
    response = requests.post(
        "https://api.github.com/graphql",
        json={"query": query},
        headers=HEADERS
    )
    if response.status_code != 200:
        raise Exception(f"Query failed: {response.text}")
    return response.json()

def fetch_repositories(language, test_mode):
    repos = []
    for upper, lower in STAR_BUCKETS:
        cursor = None
        while True:
            after_clause = f', after: "{cursor}"' if cursor else ""
            query = f"""
            {{
              search(query: "language:{language} stars:{lower}..{upper} fork:false", type: REPOSITORY, first: 100{after_clause}) {{
                pageInfo {{
                  endCursor
                  hasNextPage
                }}
                edges {{
                  node {{
                    ... on Repository {{
                      nameWithOwner
                      url
                      stargazerCount
                    }}
                  }}
                }}
              }}
            }}
            """
            result = run_query(query)
            data = result["data"]["search"]

            for edge in data["edges"]:
                repo = edge["node"]
                repos.append({
                    "name": repo["nameWithOwner"],
                    "url": repo["url"],
                    "stars": repo["stargazerCount"],
                    "language": language
                })
                if test_mode and len(repos) >= 10:
                    return repos

            if not data["pageInfo"]["hasNextPage"]:
                break
            cursor = data["pageInfo"]["endCursor"]

            if test_mode and len(repos) >= 10:
                return repos
    return repos

def main(test_mode=False):
    all_repos = []
    for lang in LANGUAGES:
        print(f"Fetching repositories for language: {lang}")
        repos = fetch_repositories(lang, test_mode)
        all_repos.extend(repos)
        if test_mode and len(all_repos) >= 10:
            break

    all_repos = all_repos[:10] if test_mode else all_repos

    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["name", "url", "stars", "language"])
        writer.writeheader()
        writer.writerows(all_repos)

    print(f"\n✅ Fetched {len(all_repos)} repositories. Saved to '{OUTPUT_CSV}'")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch GitHub repositories using GraphQL API.")
    parser.add_argument("--test", action="store_true", help="Fetch only 10 repositories total for testing.")
    args = parser.parse_args()

    main(test_mode=args.test)

