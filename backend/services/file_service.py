import os
import tempfile
from pathlib import Path
from agno.knowledge.knowledge import Knowledge
from agno.knowledge.reader.pdf_reader import PDFReader
from agno.vectordb.pineconedb import PineconeDb
from agno.knowledge.embedder.google import GeminiEmbedder
from backend.config.settings import settings
from backend.utils.chunking_utils import get_chunker

# ─── Pinecone Vector DB (shared with agent.py) ───
_vector_db = PineconeDb(
    name=settings.INDEX_NAME,
    dimension=1536,
    metric="cosine",
    spec={"serverless": {"cloud": "aws", "region": "us-east-1"}},
    api_key=settings.PINECONE_API_KEY,
    use_hybrid_search=True,
    hybrid_alpha=0.5,
    embedder=GeminiEmbedder(api_key=settings.GEMINI_API_KEY),
)

_knowledge_base = Knowledge(
    vector_db=_vector_db,
    max_results=5,
)


def get_knowledge_base() -> Knowledge:
    return _knowledge_base


async def upload_file_to_knowledge(
    file_bytes: bytes, filename: str, user_id: str
) -> None:
    """
    Saves the file to a temp location, chunks it with RecursiveChunking,
    and indexes it into Pinecone via knowledge.ainsert with user_id metadata.
    """
    suffix = Path(filename).suffix.lower()
    supported = {".pdf", ".txt", ".docx", ".md"}
    if suffix not in supported:
        raise ValueError(f"Unsupported file type: {suffix}. Supported: {supported}")

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name

    try:
        await _knowledge_base.ainsert(
            path=tmp_path,
            reader=PDFReader(
                name=f"{filename}-reader",
                chunking_strategy=get_chunker(),
            ),
            metadata={"user_id": user_id},
        )
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


async def clear_knowledge_base(user_id: str) -> None:
    """Wipes the Pinecone records belonging to a specific user."""
    try:
        _vector_db.delete_by_metadata({"user_id": user_id})
    except Exception as e:
        raise Exception(f"Failed to clear knowledge base for user {user_id}: {e}")
