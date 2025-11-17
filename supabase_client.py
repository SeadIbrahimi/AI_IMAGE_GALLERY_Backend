from supabase import create_client, Client
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://vjqobwszsgpcveoazyev.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZqcW9id3N6c2dwY3Zlb2F6eWV2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjMwMzQ5MzAsImV4cCI6MjA3ODYxMDkzMH0.ByYUBzfGBHHNr-U81hsLnRsv7jA9b18-oKT8u1EWNpg")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


