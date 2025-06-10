"""
load_project_on_pipeline.py

This script inserts project names and their associated languages into the 'Project' table of the 'arcan_pipeline' database.
It also first inserts repository details (repository name, main branch, username, and token) into the 'Repository' table.
The script:
1. Loads the database credentials from a .env file.
2. Connects to the MySQL database.
3. Inserts each repository record into the 'Repository' table and retrieves its 'id'.
4. Uses the retrieved 'id' to insert each project record into the 'Project' table.
5. Each project will have a unique id (auto-incremented), repository name, and language.
6. The 'Repository' table stores the GitHub repository details, including the branch, username, and token.

Environment:
    - A .env file containing the following variables:
        DB_HOST: Hostname of the MySQL database
        DB_NAME: Name of the MySQL database
        DB_USER: Username for the MySQL database
        DB_PASSWORD: Password for the MySQL database
        GITHUB_USERNAME: Your GitHub username
        GITHUB_TOKEN: Your GitHub Personal Access Token

Usage:
    load_project_on_pipeline.py
"""

import os
import mysql.connector
from dotenv import load_dotenv
import pandas as pd

# Load environment variables from .env file
load_dotenv()

# Retrieve database credentials from the .env file
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
GITHUB_USERNAME = os.getenv("GITHUB_USERNAME")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

# Function to insert repository data into the database and return its id
def insert_repository_data(cursor, repo_url, branch):
    try:
        # SQL query to insert data into the 'Repository' table
        insert_query = """
        INSERT INTO Repository (project_repository, branch, username, password) 
        VALUES (%s, %s, %s, %s);
        """
        
        # Insert the repository data (name, branch, username, and token)
        values = (repo_url, branch, GITHUB_USERNAME, GITHUB_TOKEN)
        cursor.execute(insert_query, values)
        
        # Return the auto-generated repository ID
        return cursor.lastrowid
    except mysql.connector.Error as e:
        print(f"Error inserting repository data: {e}")
        return None

# Function to insert project data into the database
def insert_project_data(csv_file):
    try:
        # Establishing a connection to the MySQL database
        connection = mysql.connector.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        cursor = connection.cursor()
        
        # Read the CSV file containing project data
        df = pd.read_csv(csv_file)

        # SQL query to insert data into the 'Project' table
        insert_query = """
        INSERT INTO Project (id_repository, language, name) 
        VALUES (%s, %s, %s);
        """
        
        # Iterate over the project data and insert each project into the 'Repository' and 'Project' tables
        for index, row in df.iterrows():
            # Extract repository details from the row
            repo_name = row['repository']
            language = row['language']
            repo_url = row['url']
            branch = row['branch']
    
            
            # Step 1: Insert repository data and get the repository ID
            repo_id = insert_repository_data(cursor, repo_url, branch)
            
            if repo_id:
                # Step 2: Insert project data using the repository ID
                project_values = (repo_id, language, repo_name)
                cursor.execute(insert_query, project_values)
        
        # Commit the transaction
        connection.commit()
        print(f"Successfully inserted {len(df)} projects into the 'Project' table.")
    
    except mysql.connector.Error as e:
        print(f"An error occurred: {e}")
    
    finally:
        # Close the cursor and connection
        if cursor:
            cursor.close()
        if connection:
            connection.close()

# CSV file containing project data
csv_file = 'filtered_projects.csv'
insert_project_data(csv_file)
