import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")
    PINECONE_API_KEY: str = os.getenv("PINECONE_API_KEY", "")
    INDEX_NAME: str = os.getenv("INDEX_NAME", "")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    AZURE_API_KEY: str = os.getenv("API_KEY", "")
    # gpt-4o-mini — cheap/fast model for Lead, Inventory, Directory agents
    AZURE_ENDPOINT_MINI: str = os.getenv(
        "AZURE_ENDPOINT_MINI",
        "https://crraj-mmagy8m8-eastus2.cognitiveservices.azure.com/openai/deployments/gpt-4o/chat/completions?api-version=2025-01-01-preview"
    )
    # gpt-5-nano — high-reasoning model for Researcher agent
    AZURE_ENDPOINT_NANO: str = os.getenv(
        "AZURE_ENDPOINT_NANO",
        "https://storyboardiac.cognitiveservices.azure.com/openai/deployments/gpt-5-nano/chat/completions?api-version=2025-01-01-preview"
    )
    MEMORY_DB_FILE: str = os.getenv("MEMORY_DB_FILE", "tmp/memory.db")
    MAX_MEMORY_ROWS: int = 10
    HISTORY_CONTEXT_LIMIT: int = 5

settings = Settings()
