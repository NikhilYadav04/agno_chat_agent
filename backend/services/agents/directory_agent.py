from agno.agent import Agent
from backend.services.agents.llm_factory import get_fast_llm


def build_directory_agent(mcp_tools) -> Agent:
    """
    Facility Directory Agent — handles medical center lookups.
    No JWT authentication required for these tools.
    Uses the cheap fast model.
    """
    return Agent(
        name="Directory Agent",
        role="Find nearby medical facilities or search for centers by name.",
        model=get_fast_llm(),
        tools=[mcp_tools],
        tool_call_limit=2,
        retries=1,
        instructions=(
            "Use find_nearby_medical_centers or search_medical_center_by_name as appropriate. "
            "No authentication token is needed for these tools. "
            "Return results clearly with name, address, and contact info where available."
        ),
    )
