import requests
import time
import pandas as pd

import os
from dotenv import load_dotenv
import psycopg2

from supabase import create_client, Client

# 15682 courses fetched, 13218 records with non-null average_gpa

# around x courses, 100 records max per api call
offset = 0
courses_data = []

while True:
# for i in range(0, 1): # used for testing 100 courses instead of getting all courses
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
        break

    try:
        data = r.json();
    except Exception as e:
        print(f"Failed to parse JSON at offset {offset}: {e}")
        break

    if not data:
        print("No more data. Exiting loop.")
        break

    print(f"Adding courses {offset}-{offset+100}")
    print(data)
    courses_data.extend(data)
    offset += 100

    if (offset > 30000):
        print("Offset too high. Breaking manually.")
        break



print(f"Total courses fetched: {len(courses_data)}")

## all data in courses_data, now need to get the grade distribution for each course
df = pd.DataFrame(courses_data)
# print(df.head())
# print(df.columns)
df.columns = df.columns.str.strip()
df_filtered = df[df['average_gpa'].notna()]
print(df_filtered.head())



## putting in db
print("Starting database operations...")
print(f"Attempting to insert {len(df_filtered)} records into the database")
load_dotenv()
db_url: str = os.getenv("SUPABASE_URL")
db_key: str = os.getenv("SUPABASE_KEY")


supabase: Client = create_client(db_url, db_key)

# Convert DataFrame to list of dictionaries
print("Converting DataFrame to records...")
records = df_filtered[['name', 'title', 'description', 'credits', 'average_gpa']].copy()
records['last_updated'] = pd.Timestamp.now().isoformat()  # Convert to ISO format string
records = records.rename(columns={'name': 'course_id'})  # Rename 'name' to 'course_id' to match table schema

# Convert credits to integers and handle NaN values
records['credits'] = records['credits'].fillna(0).astype(int)
records = records.replace({float('nan'): None})
records_list = records.to_dict('records')

print(f"Created {len(records_list)} records")
print("First record sample:", records_list[0])

try:
    print("Starting bulk upsert...")
    # Insert records in batches of 1000 to avoid hitting limits
    batch_size = 1000
    for i in range(0, len(records_list), batch_size):
        batch = records_list[i:i + batch_size]
        # Use upsert with course_id as the key
        result = supabase.table('courses').upsert(batch, on_conflict='course_id').execute()
        print(f"Upserted batch {i//batch_size + 1} of {(len(records_list) + batch_size - 1)//batch_size}")
    
    print(f"Successfully upserted {len(records_list)} records into the database")

except Exception as e:
    print(f"Error during upsert: {e}")