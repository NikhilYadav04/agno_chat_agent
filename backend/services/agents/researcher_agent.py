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
            """<tools>
- search_knowledge_base → user's own reports, test results, health history
- web_search           → general medical info, diseases, drug facts
  Queries must be short and conversational (e.g. "fever medicine dosing for adults")
</tools>

<rules>
- Factual and concise. Never diagnose.
- Always recommend a qualified professional for clinical decisions.
</rules>"""
        ),
    )
