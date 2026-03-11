import asyncio
import os
import sys

# Add n:/Dev/Agno to python path
sys.path.insert(0, "n:/Dev/Agno")

from backend.database.supabase_client import get_supabase

def test_fetch_id():
    supabase = get_supabase()
    response = supabase.table("chat_history").select("id").limit(1).execute()
    if response.data:
        row = response.data[0]
        print(f"ID format: {row['id']} (type: {type(row['id'])})")
    else:
        print("No data in chat_history")

if __name__ == "__main__":
    test_fetch_id()
