import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

db_url: str = os.getenv("SUPABASE_URL")
db_key: str = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(db_url, db_key)