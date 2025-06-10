"""
projects_filter.py

This script filters GitHub repository projects from a CSV file based on the metrics defined by RepoReaper 
and RepoQuester (an extension of RepoReaper). It performs the following tasks:

1. **Filters Projects**: The script filters projects where at least 5 out of the following 7 metrics:
   - community
   - documentation
   - history
   - license
   - unit_test
   - pull
   - releases
   have values greater than 0. Projects meeting this condition will be retained.

2. **Fetches Main Branch**: For each project that passes the filtering criteria, the script:
   - Fetches the name of the default (main) branch and repo URL from GitHub using the GitHub API.
   - Adds two new columns to the filtered csv: 'branch' (the main branch name) and 'url' (the repository URL).

3. **Output**: 
   - The filtered projects, along with the main branch information and URL, are saved to a new CSV file (`filtered_projects.csv`).
"""


import os
import requests
import pandas as pd
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# GitHub API Token for authentication (avoid rate limits)
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

# GitHub API base URL
GITHUB_API_URL = "https://api.github.com/repos/"

# Load the CSV file containing the project data
input_file = 'repo_quester_results.csv'  # Replace with your input CSV file
output_file = 'filtered_projects_with_details.csv'  # Output file with the new columns
THRESHOLD = 5  # Number of metrics greater than 0 required for a project to be kept

# Load the data into a pandas DataFrame
print(f"Loading data from {input_file}...")
df = pd.read_csv(input_file)
print(f"Data loaded successfully. Number of projects: {len(df)}")

# Define the columns corresponding to the metrics
metrics_columns = ['community', 'documentation', 
                   'history', 'license', 'unit_test', 'pull', 'releases']

# Function to get the main branch name and URL for a given repository
def get_repo_details(repo_name):
    try:
        url = f"{GITHUB_API_URL}{repo_name}"
        headers = {"Authorization": f"token {GITHUB_TOKEN}"}
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            repo_data = response.json()
            main_branch = repo_data['default_branch']
            repo_url = repo_data['html_url']
            return main_branch, repo_url
        else:
            print(f"Error fetching details for {repo_name}: {response.status_code}")
            return None, None
    except Exception as e:
        print(f"Error fetching data for {repo_name}: {e}")
        return None, None

# Function to check if a project has at least 'THRESHOLD' metrics with values greater than 0
def filter_project(row):
    count = sum(row[metric] > 0 for metric in metrics_columns)
    return count >= THRESHOLD

# Add the 'branch' and 'url' columns to the dataframe by fetching the main branch and URL for each project
def add_repo_details_column(df):
    branch_list = []
    url_list = []
    for repo in df['repository']:
        print(f"Fetching details for {repo}...")
        branch, url = get_repo_details(repo)
        branch_list.append(branch)
        url_list.append(url)
    df['branch'] = branch_list
    df['url'] = url_list

# Filtering the projects based on the defined threshold
print("Filtering projects based on metrics...")
filtered_df = df[df.apply(filter_project, axis=1)]
print(f"Number of projects after filtering: {len(filtered_df)}")

# Add the 'branch' and 'url' columns to the filtered dataframe
print("Adding repository details (branch and URL)...")
add_repo_details_column(filtered_df)

# Save the filtered DataFrame with the new columns to a new CSV file
filtered_df.to_csv(output_file, index=False)

print(f"Filtered projects saved to {output_file}")
