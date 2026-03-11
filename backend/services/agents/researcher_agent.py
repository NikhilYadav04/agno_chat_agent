from agno.agent import Agent
from agno.tools.wikipedia import WikipediaTools
from agno.tools.websearch import WebSearchTools
from backend.utils.knowledge_utils import knowledge_retriever
from backend.services.file_service import get_knowledge_base
from backend.services.agents.llm_factory import get_reasoning_llm


def build_researcher_agent(token: str) -> Agent:
    """
    Clinical Researcher — handles general medical questions, symptoms,
    and knowledge retrieval. Uses the high-reasoning model.
    """
    return Agent(
        name="Researcher Agent",
        role="Answer general medical and scientific questions using the personal knowledge base and web.",
        model=get_reasoning_llm(),
        tools=[
            WebSearchTools(
                enable_news=True,
                backend="google",
                enable_search=True,
                fixed_max_results=3,
                timeout=20,
            ),
        ],
        knowledge=get_knowledge_base(),
        knowledge_retriever=knowledge_retriever,
        search_knowledge=True,
        user_id=token,
        tool_call_limit=3,
        retries=2,
        instructions=(
            "Use your tools smartly: "
            "1. If the user asks about their own medical reports, test results, or health history, use `search_knowledge_base`. "
            "2. If the user asks for general medical information, diseases, or drug facts, go straight to `web_search`. "
            "3. When using web_search, generate short, natural conversational queries (e.g., 'fever medicine dosing for adults') instead of long lists of keywords. "
            "4. Be concise, factual, and medically responsible. Never diagnose. Always recommend a qualified professional for clinical decisions."
        ),
    )
