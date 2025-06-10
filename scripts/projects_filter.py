"""
projects_filter.py

This script filters projects from a CSV file based on the metrics defined by RepoReaper 
and RepoQuester (an extension of RepoReaper).
It keeps only the projects where at least 4 out of the following 7 metrics:
community, documentation, history, license, unit_test, pull, and releases
have values greater than 0. The filtered projects are then saved to a new CSV file
with the same column structure as the original file.

Usage:
    projects_filter.py
"""

import pandas as pd

# The column continuous_integration and management have all values equal to 0 --> not included in the metrics_columns

# Load the CSV file containing the project data
input_file = 'repo_quester_results.csv' 
output_file = 'filtered_projects.csv'
THRESHOLD = 5

# Load the data into a pandas DataFrame
print(f"Loading data from {input_file}...")
df = pd.read_csv(input_file)
print(f"Data loaded successfully. Number of projects: {len(df)}")

# Define the columns corresponding to the metrics
# The column continuous_integration and management have all values equal to 0 --> not included in the metrics_columns
metrics_columns = ['community', 'documentation', 
                   'history', 'license', 'unit_test', 'pull', 'releases']

# Function to check if a project has at least 6 metrics with values greater than 0
def filter_project(row):
    # Count how many metrics are greater than 0
    count = sum(row[metric] > 0 for metric in metrics_columns)
    return count >= THRESHOLD

print("Filtering projects based on metrics...")

# Apply the filter function to the DataFrame
filtered_df = df[df.apply(filter_project, axis=1)]

# Save the filtered DataFrame to a new CSV file
filtered_df.to_csv(output_file, index=False)

print(f"Filtered projects saved to {output_file}")
print(f"Number of projects after filtering: {len(filtered_df)}")
