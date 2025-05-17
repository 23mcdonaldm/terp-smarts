import requests
import time
import pandas as pd
import json

# around 13,400 professors, 100 records max per api call, ~134 total
offset = 0
courses_data = []

for i in range(0, 135):
  url = f'https://planetterp.com/api/v1/professors?type=professor&reviews=true&offset={offset}'

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

  print(f"Adding professors {offset}-{offset+100}")
  print(data)
  professors_data.extend(data)
  offset += 100

  if (offset > 15000):
    print("Offset too high. Breaking manually.")
    break



print(f"Total professors fetched: {len(professors_data)}")
print(professors_data)