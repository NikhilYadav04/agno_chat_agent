from typing import Optional
from agno.agent import Agent
from agno.knowledge.embedder.google import GeminiEmbedder
from pinecone import Pinecone
from backend.config.settings import settings

embedder = GeminiEmbedder(api_key=settings.GEMINI_API_KEY)


def knowledge_retriever(
    query: str, num_documents: int = 5, agent: Optional[Agent] = None, **kwargs
) -> Optional[list[dict]]:
    """
    Custom Pinecone retriever — filters by user_id obtained from the agent instance.
    Called automatically by Agno when search_knowledge=True.
    """
    try:
        user_id = getattr(agent, "user_id", None) if agent else kwargs.get("user_id")
        if not user_id:
            print("Error: user_id is required for Pinecone namespace filtering.")
            return None

        pc = Pinecone(api_key=settings.PINECONE_API_KEY)
        index = pc.Index("pillbin-agent-index")
        query_embedding = embedder.get_embedding(query)
        results = index.query(
            vector=query_embedding,
            top_k=num_documents,
            include_metadata=True,
            filter={"user_id": user_id},
        )
        return [match.to_dict() for match in results.matches]
    except Exception as e:
        print(f"Knowledge retrieval error: {e}")
        return None


if __name__ == "__main__":
    # Quick test
    response = knowledge_retriever(
        query="What is my blood and heart rate count", user_id="test_user_123"
    )
    print(response)
