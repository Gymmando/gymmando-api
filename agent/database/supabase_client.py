"""
Supabase database client initialization.
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from supabase import Client, create_client

# Load environment variables
# Try multiple possible .env locations
env_paths = [
    Path(__file__).parent.parent / ".env",  # agent/.env
    Path(__file__).parent.parent.parent / ".env",  # repos/gymmando-api/.env
]
for env_path in env_paths:
    if env_path.exists():
        load_dotenv(env_path)
        break
else:
    # Fallback to default .env loading
    load_dotenv()

# Initialize Supabase client
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")

if supabase_url and supabase_key:
    supabase: Client = create_client(supabase_url, supabase_key)
    print("✅ Supabase client initialized")
else:
    supabase = None
    print(
        "⚠️  Supabase credentials not found. Add SUPABASE_URL and SUPABASE_KEY to .env"
    )

