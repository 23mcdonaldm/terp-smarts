# terp-smarts
Application to determine a University of Maryland student's grades compared to expected + more.

in backend, to run the courses fetcher:

create a .env file, add in SUPABASE_URL and SUPABASE_KEY
find these in supabase dashboard -> project settings -> data api


python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

now (venv) should be displayed before your user in terminal

python3 course_fetcher.py

