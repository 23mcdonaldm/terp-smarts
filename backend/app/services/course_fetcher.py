import requests
import time
import pandas as pd

from app.db.client import supabase
from app.db.courses import bulk_upsert_courses

# 15682 courses fetched, 13218 records with non-null average_gpa

def fetch_and_update_courses():
    """Fetch courses from PlanetTerp API and update the database.
    
    Returns:
        bool: True if successful, False otherwise
    """
    # around x courses, 100 records max per api call
    offset = 0
    courses_data = []

    while True:
        url = f'https://planetterp.com/api/v1/courses?reviews=true&offset={offset}'

        try:
            r = requests.get(url, timeout=120)
        except requests.exceptions.Timeout:
            print(f"Timeout occurred at offset {offset}. Retrying...")
            continue

        if r.status_code in [500,524]:
            print(f"Received {r.status_code} timeout at offset {offset}. Retrying after delay...")
            time.sleep(5)
            continue

        if r.status_code != 200:
            print(f"Error: Received status code {r.status_code}")
            return False

        try:
            data = r.json()
        except Exception as e:
            print(f"Failed to parse JSON at offset {offset}: {e}")
            return False

        if not data:
            print("No more data. Exiting loop.")
            break

        print(f"Adding courses {offset}-{offset+100}")
        courses_data.extend(data)
        offset += 100

        if (offset > 30000):
            print("Offset too high. Breaking manually.")
            break

    print(f"Total courses fetched: {len(courses_data)}")

    # Insert all courses into database
    print("Starting database operations...")
    print(f"Attempting to insert {len(courses_data)} records into the database")

    success = bulk_upsert_courses(courses_data)
    if success:
        print("Successfully upserted all courses into the database")
        return True
    else:
        print("Failed to upsert courses into the database")
        return False