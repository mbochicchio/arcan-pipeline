"""
load_project_on_pipeline.py

This script inserts project names and their associated languages into the 'Project' table of the 'arcan_pipeline' database.
It assumes the project data (repository name and language) are stored in a CSV file.
The script:
1. Loads the database credentials from a .env file.
2. Connects to the MySQL database.
3. Inserts each project record with an incremented ID into the 'Project' table.
4. Each project will have a unique id (auto-incremented), repository name, and language.

Environment:
    - A .env file containing the following variables:
        DB_HOST: Hostname of the MySQL database
        DB_NAME: Name of the MySQL database
        DB_USER: Username for the MySQL database
        DB_PASSWORD: Password for the MySQL database

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
        INSERT INTO Project (language, name) 
        VALUES (%s, %s);
        """
        
        # Iterate over the project data and insert each project into the table
        for index, row in df.iterrows():
            # Each row contains the repository name (name) and language
            repo_name = row['repository']
            language = row['language']
            # Generate the values for the insert query (incremental id will be auto-generated)
            values = (language, repo_name)
            cursor.execute(insert_query, values)
        
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

csv_file = 'filtered_projects.csv'
insert_project_data(csv_file)