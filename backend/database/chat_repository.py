from datetime import datetime, timezone
from typing import List, Dict, Any
from backend.database.supabase_client import get_supabase
from backend.config.settings import settings

TABLE = "chat_history"


def insert_message(token: str, role: str, message: str, message_id: str = None) -> None:
    """Insert a single chat message into chat_history."""
    supabase = get_supabase()
    data = {
        "token": token,
        "role": role,
        "message": message,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    if message_id:
        data["id"] = message_id

    supabase.table(TABLE).insert(data).execute()


def fetch_recent(token: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Fetch the most recent messages for a token, returned chronologically."""
    supabase = get_supabase()
    response = (
        supabase.table(TABLE)
        .select("id, role, message, timestamp")
        .eq("token", token)
        .order("timestamp", desc=True)
        .limit(limit)
        .execute()
    )
    # Reverse so oldest → newest for agent context
    return list(reversed(response.data))


def fetch_all(token: str, page: int = 1, limit: int = 20) -> Dict[str, Any]:
    """Fetch paginated conversation history for a token, chronological order."""
    supabase = get_supabase()

    # Calculate offset
    offset = (page - 1) * limit

    # We use count="exact" to get the total number of records along with the paginated data
    response = (
        supabase.table(TABLE)
        .select("id, role, message, timestamp", count="exact")
        .eq("token", token)
        .order("timestamp", desc=False)
        .range(offset, offset + limit - 1)
        .execute()
    )

    # Supabase response object has .data and .count when we ask for count
    return {
        "data": response.data,
        "total": getattr(
            response, "count", 0
        ),  # Default fallback if count isn't retrieved
    }


def delete_all(token: str) -> None:
    """Delete all chat history for a token."""
    supabase = get_supabase()
    supabase.table(TABLE).delete().eq("token", token).execute()


def prune(token: str, max_rows: int = None) -> None:
    """
    FIFO pruning: if a token has more than max_rows records,
    delete the oldest ones until exactly max_rows remain.
    """
    if max_rows is None:
        max_rows = settings.MAX_MEMORY_ROWS

    supabase = get_supabase()
    # Fetch all IDs ordered oldest first
    response = (
        supabase.table(TABLE)
        .select("id, timestamp")
        .eq("token", token)
        .order("timestamp", desc=False)
        .execute()
    )
    rows = response.data
    excess = len(rows) - max_rows
    if excess > 0:
        ids_to_delete = [row["id"] for row in rows[:excess]]
        supabase.table(TABLE).delete().in_("id", ids_to_delete).execute()
