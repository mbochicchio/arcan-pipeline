"""
clear_tables.py

This script deletes all rows from the specified table(s) in the MySQL database.
It supports the following command-line options:

Usage:
    python clear_tables.py --table Project       # Delete all rows from the 'Project' table
    python clear_tables.py --table Repository    # Delete all rows from the 'Repository' table
    python clear_tables.py --table both          # Delete all rows from both 'Project' and 'Repository' tables

Arguments:
    --table <table_name>  The table to clear:
        'Project'         Delete rows from the 'Project' table.
        'Repository'      Delete rows from the 'Repository' table.
        'both'            Delete rows from both 'Project' and 'Repository' tables.
"""

import os
import mysql.connector
from dotenv import load_dotenv
import argparse

# Load environment variables from .env file
load_dotenv()

# Retrieve database credentials from the .env file
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

# Function to delete all rows from a specified table
def delete_all_rows(table_name):
    try:
        # Establishing a connection to the MySQL database
        connection = mysql.connector.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        cursor = connection.cursor()
        
        # SQL query to delete all rows from the specified table
        delete_query = f"DELETE FROM {table_name};"
        
        # Execute the query
        cursor.execute(delete_query)
        
        # Commit the transaction to the database
        connection.commit()
        print(f"All rows have been deleted from the '{table_name}' table.")
    
    except mysql.connector.Error as e:
        print(f"An error occurred: {e}")
    
    finally:
        # Close the cursor and connection
        if cursor:
            cursor.close()
        if connection:
            connection.close()

# Set up command-line argument parsing
def parse_args():
    parser = argparse.ArgumentParser(description="Delete rows from the Project or Repository table.")
    parser.add_argument(
        "--table", 
        choices=["Project", "Repository", "both"], 
        required=True, 
        help="Specify which table to clear: 'Project', 'Repository', or 'both'."
    )
    return parser.parse_args()

# Main function to handle the deletion logic
def main():
    args = parse_args()

    # Delete rows based on the provided table option
    if args.table == "Project":
        delete_all_rows("Project")
    elif args.table == "Repository":
        delete_all_rows("Repository")
    elif args.table == "both":
        delete_all_rows("Project")
        delete_all_rows("Repository")

if __name__ == "__main__":
    main()

