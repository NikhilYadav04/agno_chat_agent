import os
from supabase import create_client, Client
from backend.config.settings import settings

_client: Client = None

def get_supabase() -> Client:
    global _client
    if _client is None:
        if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
            raise RuntimeError("SUPABASE_URL and SUPABASE_KEY must be set in .env")
        _client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
    return _client
