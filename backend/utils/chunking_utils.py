from agno.knowledge.chunking.recursive import RecursiveChunking

def get_chunker(chunk_size: int = 200, chunk_overlap: int = 50) -> RecursiveChunking:
    """
    Returns a RecursiveChunking instance as demonstrated in test.py.
    Used for splitting large documents before indexing into Pinecone.
    """
    return RecursiveChunking(
        chunk_size=chunk_size,
        overlap=chunk_overlap,
    )
