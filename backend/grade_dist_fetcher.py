import requests
import time
import pandas as pd

import os
from dotenv import load_dotenv
import psycopg2

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

    if (offset > 15000):
        print("Offset too high. Breaking manually.")
        break



print(f"Total courses fetched: {len(courses_data)}")

## all data in courses_data, now need to get the grade distribution for each course






## putting in db

load_dotenv()
db_url = os.getenv("DATABASE_URL")

# conn = psycopg2.connect(db_url)
# cur = conn.cursor()

# cur.execute("SELECT 1;")
# print(cur.fetchone())

# conn.close()
