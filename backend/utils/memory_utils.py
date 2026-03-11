from typing import List, Dict, Any

def format_history_for_agent(history: List[Dict[str, Any]]) -> str:
    """
    Converts a list of Supabase chat_history rows into a readable
    conversation block to inject into the agent's instructions.

    Example output:
        User: What are my medicines?
        Agent: Based on your records, you are taking...
    """
    lines = []
    for entry in history:
        role = entry.get("role", "user").capitalize()
        message = entry.get("message", "").strip()
        lines.append(f"{role}: {message}")
    return "\n".join(lines)


def prune_context_string(context: str, max_chars: int = 8000) -> str:
    """
    Ensures the context string doesn't exceed max_chars.
    If it does, it truncates from the start (keeps most recent content).
    """
    if len(context) <= max_chars:
        return context
    return "[...earlier context trimmed...]\n" + context[-max_chars:]
