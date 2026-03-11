import os
from agno.db.sqlite import SqliteDb
from agno.memory import MemoryManager
from backend.services.agents.llm_factory import get_reasoning_llm
from backend.config.settings import settings

# ─── SQLite memory store ───
os.makedirs("tmp", exist_ok=True)
_sqlite_db = SqliteDb(db_file=settings.MEMORY_DB_FILE)

# ─── MemoryManager (gpt-5-nano for summarisation quality) ───
_memory_manager = MemoryManager(
    model=get_reasoning_llm(),
    db=_sqlite_db,
)


def prune_user_memories(user_id: str, max_rows: int = None) -> None:
    """FIFO pruning — keeps at most max_rows memories per user."""
    if max_rows is None:
        max_rows = settings.MAX_MEMORY_ROWS

    memories = _sqlite_db.get_user_memories(user_id=user_id)
    if len(memories) > max_rows:
        sorted_mems = sorted(
            memories, key=lambda m: m.updated_at if m.updated_at else 0
        )
        excess = len(sorted_mems) - max_rows
        for mem in sorted_mems[:excess]:
            _sqlite_db.delete_user_memory(memory_id=mem.memory_id)


def clear_all_user_memories(user_id: str) -> None:
    """Deletes all memories for a user."""
    memories = _sqlite_db.get_user_memories(user_id=user_id)
    for mem in memories:
        _sqlite_db.delete_user_memory(memory_id=mem.memory_id)
